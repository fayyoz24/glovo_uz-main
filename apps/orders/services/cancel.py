from apps.orders.models import Order
from apps.orders.constants import OrderStatus, CancelReason
from apps.orders.exceptions import OrderNotCancellable
from apps.orders.services.state_machine import transition_order_status


def cancel_order(
    *,
    order: Order,
    reason: str = CancelReason.CUSTOMER_REQUEST,
    note: str = "",
    cancelled_by=None,
) -> Order:
    if order.status not in OrderStatus.cancellable_statuses():
        raise OrderNotCancellable()

    order.cancel_reason = reason
    order.cancel_note = note
    order.save(update_fields=["cancel_reason", "cancel_note", "updated_at"])

    return transition_order_status(
        order=order,
        to_status=OrderStatus.CANCELLED,
        changed_by=cancelled_by,
        note=f"Bekor qilindi: {reason}. {note}".strip(),
    )
