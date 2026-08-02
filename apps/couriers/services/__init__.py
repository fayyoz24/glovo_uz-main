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

    # Kuryer onlayn bo'lgach, kuryer kutayotgan buyurtmalarni navbat
    # bo'yicha taklif qilishga darhol urinib ko'ramiz (5 daqiqalik retry
    # taymerini kutmasdan).
    try:
        from apps.dispatch.tasks import dispatch_waiting_orders
        dispatch_waiting_orders.delay()
    except ImportError:
        try:
            from apps.dispatch.services import dispatch_pending_orders
            dispatch_pending_orders()
        except Exception:
            pass
    except Exception:
        pass

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
    cash_collected=0,
    note: str = "",
) -> CourierEarning:
    from decimal import Decimal
    amount = Decimal(str(base_fee)) + Decimal(str(bonus)) + Decimal(str(tip))
    cash_collected = Decimal(str(cash_collected))
    earning = CourierEarning.objects.create(
        courier=courier_user,
        order=order,
        amount=amount,
        base_fee=base_fee,
        bonus=bonus,
        tip=tip,
        cash_collected=cash_collected,
        note=note,
    )
    # Profile balansi va yig'ilgan naqd pul hisobini yangilash
    update_fields = {
        "balance": models_balance_f(amount),
        "total_deliveries": models_count_f(),
    }
    if cash_collected:
        from django.db.models import F
        update_fields["total_cash_collected"] = F("total_cash_collected") + cash_collected
    CourierProfile.objects.filter(user=courier_user).update(**update_fields)

    # Joriy (aktiv) smenaning statistikasini ham yangilash — avval bu yerda
    # unutilgan edi, shu sabab kuryer ilovasidagi "shu smenada yig'ilgan
    # naqt pul" har doim 0 bo'lib ko'rinardi.
    from django.db.models import F
    shift_update = {
        "deliveries_count": F("deliveries_count") + 1,
        "total_earned": F("total_earned") + amount,
    }
    if cash_collected:
        shift_update["cash_collected"] = F("cash_collected") + cash_collected
    CourierShift.objects.filter(courier=courier_user, status=ShiftStatus.ACTIVE).update(**shift_update)

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
    updated = CourierProfile.objects.filter(
        user=courier_user,
        courier_status=CourierStatus.BUSY,
    ).update(
        courier_status=CourierStatus.ONLINE,
        updated_at=timezone.now(),
    )

    # Kuryer yetkazib berib bo'sh bo'lgach ham (xuddi go_online() dagi kabi),
    # kuryer kutayotgan buyurtmalarni navbat bo'yicha darhol taklif qilishga
    # urinamiz — 5 daqiqalik retry taymerini kutmasdan. Aks holda, allaqachon
    # tayyor turgan orderlar navbatdagi bo'sh kuryer paydo bo'lguncha "osilib"
    # qoladi.
    if updated:
        try:
            from apps.dispatch.tasks import dispatch_waiting_orders
            dispatch_waiting_orders.delay()
        except ImportError:
            try:
                from apps.dispatch.services import dispatch_pending_orders
                dispatch_pending_orders()
            except Exception:
                pass
        except Exception:
            pass
