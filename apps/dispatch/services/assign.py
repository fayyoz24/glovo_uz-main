"""
Kuryer tayinlash xizmati — asosiy dispatch algoritmi.
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.dispatch.models import CourierAssignment
from apps.dispatch.constants import (
    AssignmentStatus,
    OFFER_TIMEOUT_SECONDS,
    MAX_ASSIGNMENT_ATTEMPTS,
)
from apps.dispatch.selectors import get_scored_couriers, count_assignment_attempts
from apps.dispatch.exceptions import NoCouriersAvailable, MaxAttemptsReached


@transaction.atomic
def assign_courier_to_order(order, attempt_number: int = None) -> CourierAssignment:
    """
    Buyurtma uchun eng mos kuryerni topadi va taklif yaratadi.

    Algoritm:
    1. Filial atrofidagi onlayn kuryerlarni score bo'yicha tartiblaydi
    2. Avval rad etgan yoki allaqachon taklif qilingan kuryerlarni o'tkazib yuboradi
    3. Yangi CourierAssignment (status=OFFERED) yaratadi
    4. Kuryerga WebSocket orqali buyurtma taklifini yuboradi
    5. Celery task bilan timeout countdown ni ishga tushiradi
    """
    branch = order.branch

    if attempt_number is None:
        attempt_number = count_assignment_attempts(order) + 1

    if attempt_number > MAX_ASSIGNMENT_ATTEMPTS:
        raise MaxAttemptsReached(
            f"Order {order.public_id} uchun {MAX_ASSIGNMENT_ATTEMPTS} ta urinishdan keyin kuryer topilmadi."
        )

    # Bu order uchun ilgari rad etgan yoki vaqt tugagan kuryerlar
    excluded_courier_ids = set(
        CourierAssignment.objects.filter(
            order=order,
            status__in=[AssignmentStatus.REJECTED, AssignmentStatus.TIMED_OUT],
        ).values_list("courier_id", flat=True)
    )

    scored = get_scored_couriers(branch)
    chosen = None
    chosen_distance = None

    for entry in scored:
        if entry["courier_user"].id in excluded_courier_ids:
            continue
        chosen = entry["courier_user"]
        chosen_distance = entry["distance_km"]
        break

    if chosen is None:
        raise NoCouriersAvailable()

    offer_expires = timezone.now() + timedelta(seconds=OFFER_TIMEOUT_SECONDS)

    assignment = CourierAssignment.objects.create(
        order=order,
        courier=chosen,
        status=AssignmentStatus.OFFERED,
        attempt_number=attempt_number,
        offer_expires_at=offer_expires,
        distance_km=chosen_distance,
    )

    # Kuryerga WebSocket taklifini yuborish
    try:
        from apps.dispatch.services.realtime import send_order_offer_to_courier
        send_order_offer_to_courier(assignment=assignment)
    except Exception:
        pass

    # Timeout task ni ishga tushirish
    try:
        from apps.dispatch.tasks import handle_offer_timeout
        handle_offer_timeout.apply_async(
            args=[str(assignment.id)],
            countdown=OFFER_TIMEOUT_SECONDS + 2,
        )
    except Exception:
        pass

    return assignment


def reassign_or_escalate(order) -> CourierAssignment | None:
    """
    Tayinlash muvaffaqiyatsiz bo'lganda (rad etish / timeout):
    - Yangi kuryer qidiradi
    - Limit to'lsa admin qatoriga yuboradi
    """
    attempts = count_assignment_attempts(order)
    if attempts >= MAX_ASSIGNMENT_ATTEMPTS:
        _escalate_to_admin(order)
        return None

    try:
        return assign_courier_to_order(order, attempt_number=attempts + 1)
    except NoCouriersAvailable:
        _escalate_to_admin(order)
        return None
    except MaxAttemptsReached:
        _escalate_to_admin(order)
        return None


def _escalate_to_admin(order):
    """Admin qatoriga yuborish va bildirishnoma."""
    print(f"[DISPATCH] ESCALATE: Order {order.public_id} adminlarga yuborildi")
    try:
        from apps.dispatch.tasks import notify_admin_no_courier
        notify_admin_no_courier.delay(str(order.id))
    except Exception:
        pass
