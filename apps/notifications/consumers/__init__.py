"""
apps/notifications/consumers.py

WebSocket consumer for real-time in-app notifications.
Each authenticated user connects to their personal notification group.

URL routing example:
    path("ws/notifications/", NotificationConsumer.as_asgi())

Client connects with JWT token as query param or in first message:
    ws://host/ws/notifications/?token=<jwt>
"""
from __future__ import annotations

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Real-time notification WebSocket consumer.

    Groups:
        user_{user_id}_notifications  — per-user group
    """

    async def connect(self) -> None:
        user = self.scope.get("user")

        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_id = user.pk
        self.group_name = f"user_{self.user_id}_notifications"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send unread count on connect
        unread = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "unread_count": unread,
        }))

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data: str | None = None, bytes_data=None) -> None:
        """Handle client messages (mark_read, mark_all_read)."""
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")

        if action == "mark_read":
            notification_id = data.get("notification_id")
            if notification_id:
                success = await self._mark_read(notification_id)
                unread = await self._get_unread_count()
                await self.send(text_data=json.dumps({
                    "type": "mark_read_result",
                    "notification_id": notification_id,
                    "success": success,
                    "unread_count": unread,
                }))

        elif action == "mark_all_read":
            count = await self._mark_all_read()
            await self.send(text_data=json.dumps({
                "type": "mark_all_read_result",
                "marked": count,
                "unread_count": 0,
            }))

        elif action == "get_unread_count":
            unread = await self._get_unread_count()
            await self.send(text_data=json.dumps({
                "type": "unread_count",
                "unread_count": unread,
            }))

    # ---- Group message handlers ------------------------------- #

    async def notification_message(self, event: dict) -> None:
        """
        Called when NotificationService pushes to this user's group.
        Forwards the notification to the WebSocket client.
        """
        notif = event.get("notification", {})
        unread = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "notification": notif,
            "unread_count": unread,
        }))

    async def order_status_update(self, event: dict) -> None:
        """
        Called by order tracking consumer to push live status updates.
        """
        await self.send(text_data=json.dumps({
            "type": "order_status_update",
            "order_id": event.get("order_id"),
            "status": event.get("status"),
            "data": event.get("data", {}),
        }))

    # ---- DB helpers ------------------------------------------- #

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        from apps.notifications.selectors import get_unread_in_app_count
        return get_unread_in_app_count(self.user_id)

    @database_sync_to_async
    def _mark_read(self, notification_id: str) -> bool:
        import uuid
        from apps.notifications.services import NotificationService
        try:
            return NotificationService.mark_read(uuid.UUID(notification_id), self.user_id)
        except (ValueError, Exception):
            return False

    @database_sync_to_async
    def _mark_all_read(self) -> int:
        from apps.notifications.services import NotificationService
        return NotificationService.mark_all_read(self.user_id)
