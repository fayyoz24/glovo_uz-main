from apps.notifications.tasks import send_order_created, send_merchant_new_order
from apps.notifications.tasks import send_order_status_changed
from apps.notifications.constants import NotificationEvent

# Inside OrderService.checkout():
send_order_created.delay(
    order_id=str(order.id),
    customer_id=order.customer_id,
    context={"order_id": order.public_id, "total": str(order.total_amount)},
)
send_merchant_new_order.delay(
    order_id=str(order.id),
    merchant_owner_id=branch.merchant.owner_id,
    context={"order_id": order.public_id, "total": str(order.total_amount)},
)



# Status change event mapping
EVENT_MAP = {
    "merchant_confirmed": NotificationEvent.ORDER_MERCHANT_CONFIRMED,
    "preparing":          NotificationEvent.ORDER_PREPARING,
    "ready_for_pickup":   NotificationEvent.ORDER_READY_FOR_PICKUP,
    "courier_assigned":   NotificationEvent.ORDER_COURIER_ASSIGNED,
    "picked_up":          NotificationEvent.ORDER_PICKED_UP,
    "on_the_way":         NotificationEvent.ORDER_ON_THE_WAY,
    "delivered":          NotificationEvent.ORDER_DELIVERED,
    "cancelled":          NotificationEvent.ORDER_CANCELLED,
}

event = EVENT_MAP.get(new_status)
if event:
    send_order_status_changed.delay(
        order_id=str(order.id),
        customer_id=order.customer_id,
        event=event,
        context={"order_id": order.public_id, "reason": cancel_reason or ""},
    )