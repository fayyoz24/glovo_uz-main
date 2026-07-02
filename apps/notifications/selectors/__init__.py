"""
apps/notifications/selectors/

Read-only query layer. No business logic here.
"""
from __future__ import annotations

import uuid

from django.db.models import QuerySet

from apps.notifications.models import DeviceToken, Notification, NotificationPreference
from apps.notifications.constants import NotificationStatus


# ------------------------------------------------------------------ #
#  DeviceToken selectors                                               #
# ------------------------------------------------------------------ #

def get_active_device_tokens_for_user(user_id: int | uuid.UUID) -> QuerySet[DeviceToken]:
    """Returns all active push tokens for a user (can be multiple devices)."""
    return DeviceToken.objects.filter(user_id=user_id, is_active=True).order_by("-registered_at")


def get_device_token_by_token(token: str) -> DeviceToken | None:
    return DeviceToken.objects.filter(token=token).first()


def get_device_token_by_device_id(
    user_id: int | uuid.UUID, device_id: str, provider: str
) -> DeviceToken | None:
    return DeviceToken.objects.filter(
        user_id=user_id, device_id=device_id, provider=provider
    ).first()


# ------------------------------------------------------------------ #
#  NotificationPreference selectors                                    #
# ------------------------------------------------------------------ #

def get_or_create_notification_preference(user_id: int | uuid.UUID) -> NotificationPreference:
    pref, _ = NotificationPreference.objects.get_or_create(user_id=user_id)
    return pref


# ------------------------------------------------------------------ #
#  Notification selectors                                              #
# ------------------------------------------------------------------ #

def get_notifications_for_user(
    user_id: int | uuid.UUID,
    *,
    channel: str | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> QuerySet[Notification]:
    qs = Notification.objects.filter(recipient_id=user_id)
    if channel:
        qs = qs.filter(channel=channel)
    if unread_only:
        qs = qs.filter(read_at__isnull=True)
    return qs.order_by("-created_at")[:limit]


def get_unread_in_app_count(user_id: int | uuid.UUID) -> int:
    from apps.notifications.constants import NotificationChannel
    return Notification.objects.filter(
        recipient_id=user_id,
        channel=NotificationChannel.IN_APP,
        read_at__isnull=True,
        status=NotificationStatus.SENT,
    ).count()


def get_failed_retriable_notifications(limit: int = 100) -> QuerySet[Notification]:
    """Used by retry Celery task."""
    from django.db.models import F
    return Notification.objects.filter(
        status=NotificationStatus.FAILED,
        attempt_count__lt=F("max_attempts"),
    ).order_by("created_at")[:limit]


def get_notification_by_id(
    notification_id: uuid.UUID, user_id: int | uuid.UUID | None = None
) -> Notification | None:
    qs = Notification.objects.filter(id=notification_id)
    if user_id is not None:
        qs = qs.filter(recipient_id=user_id)
    return qs.first()


def get_notifications_for_order(order_id: uuid.UUID) -> QuerySet[Notification]:
    return Notification.objects.filter(order_id=order_id).order_by("-created_at")
