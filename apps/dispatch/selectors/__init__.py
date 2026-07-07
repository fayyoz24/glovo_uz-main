import math
from django.utils import timezone
from django.db.models import QuerySet

from apps.dispatch.models import CourierAssignment
from apps.dispatch.constants import AssignmentStatus, MAX_PING_AGE_MINUTES, MAX_SEARCH_RADIUS_KM
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


def get_nearest_couriers(branch, exclude_courier_ids=None, radius_km: float = MAX_SEARCH_RADIUS_KM) -> list[dict]:
    """
    Filial atrofidagi mavjud kuryerlarni ENG YAQINIDAN boshlab
    (sof masofa bo'yicha, radius/reyting bilan cheklamasdan) qaytaradi.

    Bu Uber/Bolt/Glovo mantig'i: doim eng yaqin bo'sh kuryerga
    birinchi bo'lib taklif boradi. `radius_km` faqat mutlaqo
    mantiqsiz (masalan, boshqa shahar/viloyatdagi) kuryerlarni
    chetlab o'tish uchun xavfsizlik cheki bo'lib xizmat qiladi.
    """
    from datetime import timedelta
    from apps.couriers.models import CourierLocationPing

    if not branch.latitude or not branch.longitude:
        return []

    exclude_courier_ids = exclude_courier_ids or set()

    branch_lat = float(branch.latitude)
    branch_lng = float(branch.longitude)

    ping_threshold = timezone.now() - timedelta(minutes=MAX_PING_AGE_MINUTES)
    recent_ping_courier_ids = (
        CourierLocationPing.objects
        .filter(recorded_at__gte=ping_threshold)
        .values_list("courier_id", flat=True)
        .distinct()
    )

    # Faol, tasdiqlangan va band bo'lmagan kuryerlar
    profiles = (
        CourierProfile.objects
        .filter(
            courier_status=CourierStatus.ONLINE,
            is_approved=True,
            user_id__in=recent_ping_courier_ids,
            current_lat__isnull=False,
            current_lng__isnull=False,
        )
        .exclude(user_id__in=exclude_courier_ids)
        .select_related("user")
    )

    nearest = []
    for profile in profiles:
        dist = _haversine_km(
            branch_lat, branch_lng,
            float(profile.current_lat),
            float(profile.current_lng),
        )
        if dist > radius_km:
            continue

        nearest.append({
            "courier_user": profile.user,
            "profile": profile,
            "distance_km": round(dist, 2),
        })

    # Faqat masofa bo'yicha — eng yaqini birinchi
    nearest.sort(key=lambda x: x["distance_km"])
    return nearest


def get_nearest_available_courier(branch, exclude_courier_ids=None) -> dict | None:
    """Eng yaqin bitta bo'sh kuryerni qaytaradi (topilmasa None)."""
    nearest = get_nearest_couriers(branch, exclude_courier_ids=exclude_courier_ids)
    return nearest[0] if nearest else None


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
