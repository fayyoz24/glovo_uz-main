"""
Django Channels orqali real-time WebSocket xabarlari.
"""
import json


def send_order_offer_to_courier(assignment):
    """
    Kuryerga WebSocket orqali buyurtma taklifini yuboradi.
    Consumer: CourierConsumer (channels app)
    Group name: courier_{user_id}
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        group_name = f"courier_{assignment.courier_id}"

        order = assignment.order
        payload = {
            "type": "order.offer",
            "assignment_id": str(assignment.id),
            "order": {
                "id": str(order.id),
                "public_id": order.public_id,
                "merchant_name": order.merchant.name,
                "branch_name": order.branch.name,
                "address": order.address_snapshot,
                "total_amount": str(order.total_amount),
                "distance_km": assignment.distance_km,
                "payment_method": order.payment_method,
            },
            "expires_in_seconds": 30,
        }

        async_to_sync(channel_layer.group_send)(group_name, payload)
    except Exception as e:
        print(f"[REALTIME] send_order_offer failed: {e}")


def broadcast_courier_location(*, courier_user, lat: float, lng: float):
    """
    Kuryer joylashuvini mijozga real-time yuboradi.
    Faqat kuryer faol buyurtmaga ega bo'lsa ishlaydi.
    Group name: order_{order_id}
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from apps.orders.models import Order
        from apps.orders.constants import OrderStatus

        active_orders = Order.objects.filter(
            courier=courier_user,
            status__in=[OrderStatus.PICKED_UP, OrderStatus.ON_THE_WAY, OrderStatus.COURIER_ASSIGNED],
        ).values_list("id", flat=True)

        if not active_orders:
            return

        channel_layer = get_channel_layer()
        for order_id in active_orders:
            group_name = f"order_{order_id}"
            payload = {
                "type": "courier.location",
                "courier_id": str(courier_user.id),
                "lat": lat,
                "lng": lng,
            }
            async_to_sync(channel_layer.group_send)(group_name, payload)
    except Exception as e:
        print(f"[REALTIME] broadcast_courier_location failed: {e}")


def send_order_status_update(*, order):
    """
    Buyurtma holati o'zgarganda mijozga WebSocket xabar yuboradi.
    Group name: order_{order_id}
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        group_name = f"order_{order.id}"

        payload = {
            "type": "order.status",
            "order_id": str(order.id),
            "status": order.status,
            "public_id": order.public_id,
        }
        async_to_sync(channel_layer.group_send)(group_name, payload)
    except Exception as e:
        print(f"[REALTIME] send_order_status_update failed: {e}")
