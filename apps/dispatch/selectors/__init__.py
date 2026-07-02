import math
from django.utils import timezone
from django.db.models import QuerySet

from apps.dispatch.models import CourierAssignment
from apps.dispatch.constants import AssignmentStatus, MAX_PING_AGE_MINUTES
from apps.couriers.models import CourierProfile
from apps.couriers.constants import CourierStatus


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ikkita koordinata orasidagi masofani km da hisoblaydi."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_scored_couriers(branch, radius_km: float = 3.0) -> list[dict]:
    """
    Filialga yaqin va tayinlash uchun mos kuryerlarni
    hisob (score) bo'yicha saralangan ro'yxat sifatida qaytaradi.

    Score formulasi:
        score = (1 / distance_km) * 0.5
              + rating_normalized * 0.3
              + idle_bonus * 0.2

    Kichikroq distance → yuqori score.
    """
    from datetime import timedelta
    from apps.couriers.models import CourierLocationPing

    if not branch.latitude or not branch.longitude:
        return []

    branch_lat = float(branch.latitude)
    branch_lng = float(branch.longitude)

    ping_threshold = timezone.now() - timedelta(minutes=MAX_PING_AGE_MINUTES)
    recent_ping_courier_ids = (
        CourierLocationPing.objects
        .filter(recorded_at__gte=ping_threshold)
        .values_list("courier_id", flat=True)
        .distinct()
    )

    # Faol va mavjud kuryerlar
    profiles = (
        CourierProfile.objects
        .filter(
            courier_status=CourierStatus.ONLINE,
            is_approved=True,
            user_id__in=recent_ping_courier_ids,
            current_lat__isnull=False,
            current_lng__isnull=False,
        )
        .select_related("user")
    )

    scored = []
    for profile in profiles:
        dist = _haversine_km(
            branch_lat, branch_lng,
            float(profile.current_lat),
            float(profile.current_lng),
        )
        if dist > radius_km:
            continue

        # Masofaga asosiy hissa (yaqin = yaxshi)
        distance_score = 1.0 / max(dist, 0.1)
        # Rating (5 dan normallashtirish)
        rating_score = float(profile.rating) / 5.0
        # Idle bonus — ko'p yetkazib bergan kuryer kamroq priority
        idle_score = 1.0 / max(profile.total_deliveries, 1)

        total_score = distance_score * 0.5 + rating_score * 0.3 + idle_score * 0.2

        scored.append({
            "courier_user": profile.user,
            "profile": profile,
            "distance_km": round(dist, 2),
            "score": round(total_score, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def get_active_assignment(order) -> CourierAssignment | None:
    return CourierAssignment.objects.filter(
        order=order,
        status=AssignmentStatus.OFFERED,
    ).select_related("courier").first()


def get_assignment_for_courier(assignment_id, courier_user) -> CourierAssignment:
    from apps.dispatch.exceptions import AssignmentNotFound
    try:
        return CourierAssignment.objects.select_related("order__branch__merchant").get(
            id=assignment_id,
            courier=courier_user,
        )
    except CourierAssignment.DoesNotExist:
        raise AssignmentNotFound()


def count_assignment_attempts(order) -> int:
    return CourierAssignment.objects.filter(order=order).count()


def get_expired_offers() -> QuerySet:
    """Muddati o'tgan aktiv takliflar."""
    return CourierAssignment.objects.filter(
        status=AssignmentStatus.OFFERED,
        offer_expires_at__lt=timezone.now(),
    ).select_related("order__branch", "courier")
