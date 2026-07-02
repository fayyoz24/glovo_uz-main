"""
Kuryer yetkazib berish jarayoni: olib ketdi / yetkazdi.
"""
from django.db import transaction
from django.utils import timezone

from apps.dispatch.models import CourierAssignment
from apps.dispatch.constants import AssignmentStatus
from apps.orders.constants import OrderStatus
from apps.orders.services import transition_order_status
from apps.couriers.services import set_courier_available, record_delivery_earning


@transaction.atomic
def courier_picked_up(*, courier_user, order):
    """Kuryer buyurtmani olib ketdi."""
    transition_order_status(
        order=order,
        to_status=OrderStatus.PICKED_UP,
        changed_by=courier_user,
        note="Kuryer buyurtmani oldi",
    )

    # on_the_way ham shu yerda yoki alohida endpoint
    # Hozirda picked_up → on_the_way ni auto o'tkazamiz
    transition_order_status(
        order=order,
        to_status=OrderStatus.ON_THE_WAY,
        changed_by=courier_user,
        note="Kuryer yo'lda",
    )
    return order


@transaction.atomic
def courier_delivered(*, courier_user, order):
    """Kuryer buyurtmani yetkazdi."""
    transition_order_status(
        order=order,
        to_status=OrderStatus.DELIVERED,
        changed_by=courier_user,
        note="Yetkazib berildi",
    )

    # Assignment ni COMPLETED qilish
    CourierAssignment.objects.filter(
        order=order,
        courier=courier_user,
        status=AssignmentStatus.ACCEPTED,
    ).update(status=AssignmentStatus.COMPLETED, completed_at=timezone.now())

    # Kuryerni yana ONLINE qilish
    set_courier_available(courier_user=courier_user)

    # Daromad yozuvi
    _create_earning_for_delivery(courier_user=courier_user, order=order)

    return order


def _create_earning_for_delivery(courier_user, order):
    """Yetkazish uchun daromad hisoblaydi va yozadi."""
    from decimal import Decimal
    base_fee = order.delivery_fee * Decimal("0.8")  # 80% kuryerga
    tip = order.tip_amount
    try:
        record_delivery_earning(
            courier_user=courier_user,
            order=order,
            base_fee=base_fee,
            bonus=Decimal("0"),
            tip=tip,
        )
    except Exception as e:
        print(f"[DISPATCH] Earning error: {e}")
