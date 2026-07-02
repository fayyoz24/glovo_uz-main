from django.db import transaction
from django.utils import timezone

from apps.couriers.models import CourierProfile, CourierLocationPing, CourierShift, CourierEarning
from apps.couriers.selectors import get_courier_profile, get_active_shift
from apps.couriers.constants import CourierStatus, ShiftStatus
from apps.couriers.exceptions import (
    CourierAlreadyOnline,
    CourierAlreadyOffline,
    CourierNotOnline,
    ActiveShiftExists,
)


@transaction.atomic
def go_online(*, user) -> CourierProfile:
    profile = get_courier_profile(user)

    if profile.courier_status == CourierStatus.ONLINE:
        raise CourierAlreadyOnline()

    # Faol smena bor-yo'qligini tekshirish
    existing_shift = get_active_shift(user)
    if existing_shift:
        raise ActiveShiftExists()

    profile.courier_status = CourierStatus.ONLINE
    profile.save(update_fields=["courier_status", "updated_at"])

    CourierShift.objects.create(courier=user, status=ShiftStatus.ACTIVE)
    return profile


@transaction.atomic
def go_offline(*, user) -> CourierProfile:
    profile = get_courier_profile(user)

    if profile.courier_status == CourierStatus.OFFLINE:
        raise CourierAlreadyOffline()

    profile.courier_status = CourierStatus.OFFLINE
    profile.save(update_fields=["courier_status", "updated_at"])

    # Faol smenani yopish
    shift = get_active_shift(user)
    if shift:
        shift.status = ShiftStatus.ENDED
        shift.end_time = timezone.now()
        shift.save(update_fields=["status", "end_time"])

    return profile


def record_location_ping(*, user, latitude: float, longitude: float, accuracy: float = None):
    """Kuryer joylashuvini yangilaydi va ping yozadi."""
    ping = CourierLocationPing.objects.create(
        courier=user,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
    )
    # Profile dagi oxirgi lokatsiyani yangilash
    CourierProfile.objects.filter(user=user).update(
        current_lat=latitude,
        current_lng=longitude,
        last_location_at=timezone.now(),
    )

    # Channels orqali real-time broadcastuvchi order bo'lsa event yuborish
    try:
        from apps.dispatch.services import broadcast_courier_location
        broadcast_courier_location(courier_user=user, lat=latitude, lng=longitude)
    except ImportError:
        pass

    return ping


@transaction.atomic
def record_delivery_earning(
    *,
    courier_user,
    order,
    base_fee,
    bonus=0,
    tip=0,
    note: str = "",
) -> CourierEarning:
    from decimal import Decimal
    amount = Decimal(str(base_fee)) + Decimal(str(bonus)) + Decimal(str(tip))
    earning = CourierEarning.objects.create(
        courier=courier_user,
        order=order,
        amount=amount,
        base_fee=base_fee,
        bonus=bonus,
        tip=tip,
        note=note,
    )
    # Profile balansini yangilash
    CourierProfile.objects.filter(user=courier_user).update(
        balance=models_balance_f(amount),
        total_deliveries=models_count_f(),
    )
    return earning


def models_balance_f(amount):
    from django.db.models import F
    return F("balance") + amount


def models_count_f():
    from django.db.models import F
    return F("total_deliveries") + 1


def set_courier_busy(*, courier_user):
    CourierProfile.objects.filter(user=courier_user).update(
        courier_status=CourierStatus.BUSY,
        updated_at=timezone.now(),
    )


def set_courier_available(*, courier_user):
    CourierProfile.objects.filter(
        user=courier_user,
        courier_status=CourierStatus.BUSY,
    ).update(
        courier_status=CourierStatus.ONLINE,
        updated_at=timezone.now(),
    )
