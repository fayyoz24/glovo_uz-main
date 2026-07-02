"""
Django Channels WebSocket consumers.

Routing (asgi.py / routing.py ga qo'shiladi):

    from django.urls import re_path
    from apps.dispatch.consumers import CourierConsumer, OrderTrackingConsumer

    websocket_urlpatterns = [
        re_path(r"ws/courier/$", CourierConsumer.as_asgi()),
        re_path(r"ws/orders/(?P<order_id>[0-9a-f-]+)/$", OrderTrackingConsumer.as_asgi()),
    ]
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CourierConsumer(AsyncWebsocketConsumer):
    """
    Kuryer uchun WebSocket consumer.
    - Buyurtma takliflarini qabul qiladi
    - Holat yangilanishlarini oladi
    Group: courier_{user_id}
    """

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"courier_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(json.dumps({"type": "connected", "message": "Kuryer ulandi"}))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Kuryerdan kelgan xabarlar (heartbeat)."""
        try:
            data = json.loads(text_data or "{}")
            if data.get("type") == "ping":
                await self.send(json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass

    # ─── Group message handlers ───────────────────────────────────────

    async def order_offer(self, event):
        """Yangi buyurtma taklifi."""
        await self.send(json.dumps({
            "type": "order.offer",
            "assignment_id": event["assignment_id"],
            "order": event["order"],
            "expires_in_seconds": event.get("expires_in_seconds", 30),
        }))

    async def order_status(self, event):
        """Buyurtma holati yangilandi."""
        await self.send(json.dumps({
            "type": "order.status",
            "order_id": event["order_id"],
            "status": event["status"],
        }))


class OrderTrackingConsumer(AsyncWebsocketConsumer):
    """
    Mijoz uchun buyurtma kuzatuv consumer.
    - Kuryer joylashuvini real-time ko'radi
    - Buyurtma holati yangilanishlarini oladi
    Group: order_{order_id}
    """

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.order_id}"

        # Buyurtma foydalanuvchiga tegishli ekanligini tekshirish
        from channels.db import database_sync_to_async
        owns = await database_sync_to_async(self._check_order_ownership)(user)
        if not owns:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    def _check_order_ownership(self, user) -> bool:
        from apps.orders.models import Order
        return Order.objects.filter(id=self.order_id, customer=user).exists()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
            if data.get("type") == "ping":
                await self.send(json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass

    # ─── Group message handlers ───────────────────────────────────────

    async def courier_location(self, event):
        """Kuryer joylashuvi yangilandi."""
        await self.send(json.dumps({
            "type": "courier.location",
            "lat": event["lat"],
            "lng": event["lng"],
        }))

    async def order_status(self, event):
        """Buyurtma holati o'zgardi."""
        await self.send(json.dumps({
            "type": "order.status",
            "status": event["status"],
            "order_id": event["order_id"],
        }))
