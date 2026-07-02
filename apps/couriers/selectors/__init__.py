from django.db.models import QuerySet, Sum
from django.utils import timezone
from datetime import timedelta

from apps.couriers.models import CourierProfile, CourierLocationPing, CourierShift, CourierEarning
from apps.couriers.constants import CourierStatus, ShiftStatus


def get_courier_profile(user) -> CourierProfile:
    from apps.couriers.exceptions import CourierProfileNotFound
    try:
        return CourierProfile.objects.select_related("user").get(user=user)
    except CourierProfile.DoesNotExist:
        raise CourierProfileNotFound()


def get_active_shift(courier_user) -> CourierShift | None:
    return CourierShift.objects.filter(
        courier=courier_user,
        status=ShiftStatus.ACTIVE,
    ).first()


def get_courier_earnings_summary(courier_user, days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    qs = CourierEarning.objects.filter(courier=courier_user, created_at__gte=since)
    agg = qs.aggregate(
        total=Sum("amount"),
        base=Sum("base_fee"),
        bonus=Sum("bonus"),
        tips=Sum("tip"),
    )
    return {
        "total": agg["total"] or 0,
        "base_fee": agg["base"] or 0,
        "bonus": agg["bonus"] or 0,
        "tips": agg["tips"] or 0,
        "deliveries": qs.count(),
        "period_days": days,
    }


def get_courier_earnings_list(courier_user, page_size: int = 20) -> QuerySet:
    return CourierEarning.objects.filter(
        courier=courier_user
    ).select_related("order").order_by("-created_at")[:page_size]


def get_latest_location(courier_user) -> CourierLocationPing | None:
    return CourierLocationPing.objects.filter(courier=courier_user).first()


def get_available_couriers_near_branch(branch, radius_km: float = 3.0, max_age_minutes: int = 5):
    """
    Filialga yaqin mavjud kuryerlarni qaytaradi.
    Haqiqiy geo-filter dispatch/selectors.py da amalga oshiriladi —
    bu yerda sodda versiya (distance filteri DB darajasida PostGIS bilan ishlaydi).
    """
    threshold = timezone.now() - timedelta(minutes=max_age_minutes)
    recent_pings = CourierLocationPing.objects.filter(
        recorded_at__gte=threshold
    ).values_list("courier_id", flat=True).distinct()

    return CourierProfile.objects.filter(
        courier_status=CourierStatus.ONLINE,
        is_approved=True,
        user_id__in=recent_pings,
    ).select_related("user")
