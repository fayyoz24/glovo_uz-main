from apps.notifications.tasks import send_courier_order_offer

send_courier_order_offer.delay(
    order_id=str(order.id),
    courier_user_id=courier.user_id,
    context={
        "merchant_name": order.branch.merchant.name,
        "distance": "1.2",
        "amount": str(order.total_amount),
    },
)