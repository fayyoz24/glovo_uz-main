"""
Order holat mashinasi — faqat ruxsat etilgan o'tishlarni amalga oshiradi.
"""
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderStatusHistory
from apps.orders.constants import OrderStatus
from apps.orders.exceptions import OrderNotFound, InvalidOrderTransition


TIMESTAMP_FIELDS = {
    OrderStatus.MERCHANT_CONFIRMED: "confirmed_at",
    OrderStatus.PICKED_UP: "picked_up_at",
    OrderStatus.DELIVERED: "delivered_at",
    OrderStatus.CANCELLED: "cancelled_at",
}


@transaction.atomic
def transition_order_status(
    *,
    order: Order,
    to_status: str,
    changed_by=None,
    note: str = "",
) -> Order:
    allowed = OrderStatus.transitions().get(order.status, [])
    if to_status not in allowed:
        raise InvalidOrderTransition(
            detail=f"'{order.status}' holatidan '{to_status}' holatiga o'tish ruxsat etilmagan."
        )

    from_status = order.status
    order.status = to_status

    # Tegishli timestamp ni o'rnatish
    ts_field = TIMESTAMP_FIELDS.get(to_status)
    if ts_field:
        setattr(order, ts_field, timezone.now())

    order.save()

    OrderStatusHistory.objects.create(
        order=order,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        note=note,
    )

    # Async bildirishnomalar
    try:
        from apps.orders.tasks import notify_order_status_changed
        notify_order_status_changed.delay(str(order.id), to_status)
    except ImportError:
        pass

    return order
