"""
apps/notifications/services/

All business logic lives here. Views and tasks call services only.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.notifications.constants import (
    NOTIFICATION_EVENT_CHANNELS,
    NOTIFICATION_EVENT_TEMPLATES,
    NotificationChannel,
    NotificationEvent,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.exceptions import (
    InvalidDeviceTokenError,
    NotificationError,
    NotificationOptedOutError,
    TemplateRenderError,
)
from apps.notifications.models import DeviceToken, Notification, NotificationPreference
from apps.notifications.providers import (
    DjangoEmailProvider,
    EmailMessage,
    FCMProvider,
    PushMessage,
    SMSMessage,
    TelegramMessage,
    TelegramProvider,
    get_email_provider,
    get_push_provider,
    get_sms_provider,
    get_telegram_provider,
)
from apps.notifications.selectors import (
    get_active_device_tokens_for_user,
    get_or_create_notification_preference,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Template helpers                                                    #
# ------------------------------------------------------------------ #

def _render_template(event: str, lang: str, context: dict) -> tuple[str, str]:
    """
    Returns (title, body) for the given event and language.
    Falls back to 'uz' if lang not found.
    """
    tmpl = NOTIFICATION_EVENT_TEMPLATES.get(event)
    if not tmpl:
        raise TemplateRenderError(f"No template for event: {event}")

    lang = lang if lang in ("uz", "ru") else "uz"
    title = tmpl.get(f"title_{lang}", tmpl.get("title_uz", ""))
    body_tmpl = tmpl.get(f"body_{lang}", tmpl.get("body_uz", ""))

    try:
        body = body_tmpl.format(**context)
        title = title.format(**context) if title else title
    except KeyError as exc:
        raise TemplateRenderError(
            f"Missing context key {exc} for event {event}"
        ) from exc

    return title, body


# ------------------------------------------------------------------ #
#  DeviceToken service                                                 #
# ------------------------------------------------------------------ #

class DeviceTokenService:
    @staticmethod
    def register(
        user_id: int | uuid.UUID,
        token: str,
        provider: str,
        device_id: str = "",
        device_name: str = "",
        app_version: str = "",
    ) -> DeviceToken:
        """
        Upsert device token. If device_id matches an existing record, update it.
        Deactivate old tokens for the same device_id / provider combo.
        """
        with transaction.atomic():
            # Deactivate any old tokens for same device
            if device_id:
                DeviceToken.objects.filter(
                    user_id=user_id,
                    device_id=device_id,
                    provider=provider,
                ).exclude(token=token).update(is_active=False)

            obj, _ = DeviceToken.objects.update_or_create(
                user_id=user_id,
                device_id=device_id or token[:64],
                provider=provider,
                defaults={
                    "token": token,
                    "device_name": device_name,
                    "app_version": app_version,
                    "is_active": True,
                },
            )
        return obj

    @staticmethod
    def deregister(token: str) -> None:
        DeviceToken.objects.filter(token=token).update(is_active=False)

    @staticmethod
    def deregister_invalid(token: str) -> None:
        """Called when provider returns InvalidRegistration."""
        DeviceToken.objects.filter(token=token).update(is_active=False)
        logger.warning("Deregistered invalid push token: %s…", token[:20])


# ------------------------------------------------------------------ #
#  NotificationPreference service                                      #
# ------------------------------------------------------------------ #

class NotificationPreferenceService:
    @staticmethod
    def update(user_id: int | uuid.UUID, **kwargs) -> NotificationPreference:
        pref = get_or_create_notification_preference(user_id)
        allowed_fields = {
            "push_enabled", "sms_enabled", "email_enabled", "in_app_enabled",
            "promotional_push", "promotional_sms", "promotional_email",
        }
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(pref, key, value)
        pref.save()
        return pref


# ------------------------------------------------------------------ #
#  Core dispatch service                                               #
# ------------------------------------------------------------------ #

class NotificationService:
    """
    Primary entry point for sending notifications.
    Callers (tasks, order service, courier service, etc.) use send_event().
    """

    # ---- Public API ------------------------------------------- #

    @classmethod
    def send_event(
        cls,
        event: str,
        recipient_id: int | uuid.UUID,
        context: dict,
        *,
        notification_type: str = NotificationType.TRANSACTIONAL,
        order_id: uuid.UUID | None = None,
        phone: str | None = None,
        email: str | None = None,
        telegram_chat_id: str | None = None,
        lang: str = "uz",
        extra_data: dict | None = None,
    ) -> list[Notification]:
        """
        Dispatches all channel notifications for the given event.
        Returns list of created Notification rows.

        This is called from Celery tasks (async), not from views directly.
        """
        channels = NOTIFICATION_EVENT_CHANNELS.get(event, [])
        if not channels:
            logger.warning("No channels configured for event: %s", event)
            return []

        pref = get_or_create_notification_preference(recipient_id)
        notifications = []

        for channel in channels:
            if not pref.is_channel_enabled(channel, notification_type):
                logger.debug(
                    "Notification opted out: user=%s event=%s channel=%s",
                    recipient_id, event, channel,
                )
                continue

            try:
                title, body = _render_template(event, lang, context)
            except TemplateRenderError:
                logger.exception("Template render failed: event=%s", event)
                continue

            notif = cls._dispatch_channel(
                event=event,
                channel=channel,
                recipient_id=recipient_id,
                title=title,
                body=body,
                notification_type=notification_type,
                order_id=order_id,
                phone=phone,
                email=email,
                telegram_chat_id=telegram_chat_id,
                extra_data=extra_data or {},
            )
            if notif:
                notifications.append(notif)

        return notifications

    # ---- Internal channel dispatch ---------------------------- #

    @classmethod
    def _dispatch_channel(
        cls,
        event: str,
        channel: str,
        recipient_id: int | uuid.UUID,
        title: str,
        body: str,
        notification_type: str,
        order_id: uuid.UUID | None,
        phone: str | None,
        email: str | None,
        telegram_chat_id: str | None,
        extra_data: dict,
    ) -> Notification | None:

        if channel == NotificationChannel.PUSH:
            return cls._send_push(
                event, recipient_id, title, body,
                notification_type, order_id, extra_data,
            )
        elif channel == NotificationChannel.SMS:
            return cls._send_sms(
                event, recipient_id, body,
                notification_type, order_id, phone,
            )
        elif channel == NotificationChannel.EMAIL:
            return cls._send_email(
                event, recipient_id, title, body,
                notification_type, order_id, email,
            )
        elif channel == NotificationChannel.IN_APP:
            return cls._create_in_app(
                event, recipient_id, title, body,
                notification_type, order_id, extra_data,
            )
        elif channel == NotificationChannel.TELEGRAM:
            return cls._send_telegram(
                event, recipient_id, body,
                notification_type, order_id, telegram_chat_id,
            )
        logger.warning("Unknown channel: %s", channel)
        return None

    # ---- Push ------------------------------------------------- #

    @classmethod
    def _send_push(
        cls,
        event: str,
        recipient_id: int | uuid.UUID,
        title: str,
        body: str,
        notification_type: str,
        order_id: uuid.UUID | None,
        data: dict,
    ) -> Notification | None:
        tokens = get_active_device_tokens_for_user(recipient_id)
        if not tokens.exists():
            logger.debug("No push tokens for user %s", recipient_id)
            return None

        # Send to all devices, log each attempt
        last_notif = None
        for device in tokens:
            notif = Notification.objects.create(
                recipient_id=recipient_id,
                event=event,
                channel=NotificationChannel.PUSH,
                notification_type=notification_type,
                title=title,
                body=body,
                data=data,
                push_token=device.token,
                order_id=order_id,
                status=NotificationStatus.PENDING,
            )
            try:
                provider = get_push_provider()
                result = provider.send(
                    PushMessage(
                        token=device.token,
                        title=title,
                        body=body,
                        data={**data, "event": event, "order_id": str(order_id or "")},
                    )
                )
                notif.status = NotificationStatus.SENT
                notif.provider_message_id = result.provider_message_id
                notif.sent_at = timezone.now()
                device.last_used_at = timezone.now()
                device.save(update_fields=["last_used_at"])

            except InvalidDeviceTokenError:
                DeviceTokenService.deregister_invalid(device.token)
                notif.status = NotificationStatus.FAILED
                notif.failure_reason = "invalid_token"
                notif.attempt_count += 1

            except NotificationError as exc:
                notif.status = NotificationStatus.FAILED
                notif.failure_reason = str(exc)
                notif.attempt_count += 1
                logger.warning("Push failed for user %s: %s", recipient_id, exc)

            notif.save()
            last_notif = notif

        return last_notif

    # ---- SMS -------------------------------------------------- #

    @classmethod
    def _send_sms(
        cls,
        event: str,
        recipient_id: int | uuid.UUID,
        body: str,
        notification_type: str,
        order_id: uuid.UUID | None,
        phone: str | None,
    ) -> Notification | None:
        if not phone:
            logger.warning("SMS requested but no phone for user %s", recipient_id)
            return None

        notif = Notification.objects.create(
            recipient_id=recipient_id,
            event=event,
            channel=NotificationChannel.SMS,
            notification_type=notification_type,
            body=body,
            phone_number=phone,
            order_id=order_id,
            status=NotificationStatus.PENDING,
        )
        try:
            provider = get_sms_provider()
            result = provider.send(SMSMessage(phone=phone, text=body))
            notif.status = NotificationStatus.SENT
            notif.provider_message_id = result.provider_message_id
            notif.sent_at = timezone.now()
        except NotificationError as exc:
            notif.status = NotificationStatus.FAILED
            notif.failure_reason = str(exc)
            notif.attempt_count += 1
            logger.warning("SMS failed for user %s: %s", recipient_id, exc)

        notif.save()
        return notif

    # ---- Email ------------------------------------------------ #

    @classmethod
    def _send_email(
        cls,
        event: str,
        recipient_id: int | uuid.UUID,
        title: str,
        body: str,
        notification_type: str,
        order_id: uuid.UUID | None,
        email: str | None,
    ) -> Notification | None:
        if not email:
            return None

        notif = Notification.objects.create(
            recipient_id=recipient_id,
            event=event,
            channel=NotificationChannel.EMAIL,
            notification_type=notification_type,
            title=title,
            body=body,
            email_address=email,
            order_id=order_id,
            status=NotificationStatus.PENDING,
        )
        try:
            provider = get_email_provider()
            provider.send(
                EmailMessage(to=email, subject=title, body_html=body, body_text=body)
            )
            notif.status = NotificationStatus.SENT
            notif.sent_at = timezone.now()
        except NotificationError as exc:
            notif.status = NotificationStatus.FAILED
            notif.failure_reason = str(exc)
            notif.attempt_count += 1

        notif.save()
        return notif

    # ---- In-App ----------------------------------------------- #

    @classmethod
    def _create_in_app(
        cls,
        event: str,
        recipient_id: int | uuid.UUID,
        title: str,
        body: str,
        notification_type: str,
        order_id: uuid.UUID | None,
        data: dict,
    ) -> Notification:
        """
        In-app notifications are stored and delivered via WebSocket consumer.
        """
        notif = Notification.objects.create(
            recipient_id=recipient_id,
            event=event,
            channel=NotificationChannel.IN_APP,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
            order_id=order_id,
            status=NotificationStatus.SENT,
            sent_at=timezone.now(),
        )
        # Push to WebSocket channel layer for real-time delivery
        cls._push_to_channel_layer(recipient_id, notif)
        return notif

    @staticmethod
    def _push_to_channel_layer(
        recipient_id: int | uuid.UUID,
        notif: Notification,
    ) -> None:
        """Send in-app notification to user's WebSocket group."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer is None:
                return

            group_name = f"user_{recipient_id}_notifications"
            payload = {
                "type": "notification.message",
                "notification": {
                    "id": str(notif.id),
                    "event": notif.event,
                    "title": notif.title,
                    "body": notif.body,
                    "data": notif.data,
                    "order_id": str(notif.order_id) if notif.order_id else None,
                    "created_at": notif.created_at.isoformat(),
                },
            }
            async_to_sync(channel_layer.group_send)(group_name, payload)
        except Exception as exc:
            logger.warning("Channel layer push failed: %s", exc)

    # ---- Telegram --------------------------------------------- #

    @classmethod
    def _send_telegram(
        cls,
        event: str,
        recipient_id: int | uuid.UUID,
        body: str,
        notification_type: str,
        order_id: uuid.UUID | None,
        chat_id: str | None,
    ) -> Notification | None:
        from django.conf import settings

        effective_chat_id = chat_id or getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)
        if not effective_chat_id:
            return None

        notif = Notification.objects.create(
            recipient_id=recipient_id,
            event=event,
            channel=NotificationChannel.TELEGRAM,
            notification_type=notification_type,
            body=body,
            order_id=order_id,
            status=NotificationStatus.PENDING,
        )
        try:
            provider = get_telegram_provider()
            result = provider.send(TelegramMessage(chat_id=effective_chat_id, text=body))
            notif.status = NotificationStatus.SENT
            notif.provider_message_id = result.provider_message_id
            notif.sent_at = timezone.now()
        except NotificationError as exc:
            notif.status = NotificationStatus.FAILED
            notif.failure_reason = str(exc)
            notif.attempt_count += 1
            logger.warning("Telegram failed: %s", exc)

        notif.save()
        return notif

    # ---- Mark read -------------------------------------------- #

    @staticmethod
    def mark_read(notification_id: uuid.UUID, user_id: int | uuid.UUID) -> bool:
        updated = Notification.objects.filter(
            id=notification_id,
            recipient_id=user_id,
            read_at__isnull=True,
        ).update(read_at=timezone.now())
        return updated > 0

    @staticmethod
    def mark_all_read(user_id: int | uuid.UUID) -> int:
        from apps.notifications.constants import NotificationChannel as NC
        return Notification.objects.filter(
            recipient_id=user_id,
            channel=NC.IN_APP,
            read_at__isnull=True,
        ).update(read_at=timezone.now())

    # ---- Retry failed ----------------------------------------- #

    @classmethod
    def retry_notification(cls, notif: Notification) -> bool:
        """
        Retry a single failed notification. Returns True if sent successfully.
        Called from the retry Celery task.
        """
        if not notif.is_retriable:
            return False

        if notif.channel == NotificationChannel.PUSH:
            tokens = get_active_device_tokens_for_user(notif.recipient_id)
            if not tokens.exists():
                notif.status = NotificationStatus.FAILED
                notif.failure_reason = "no_active_tokens"
                notif.save()
                return False
            try:
                provider = get_push_provider()
                result = provider.send(
                    PushMessage(
                        token=notif.push_token,
                        title=notif.title,
                        body=notif.body,
                        data=notif.data,
                    )
                )
                notif.status = NotificationStatus.SENT
                notif.provider_message_id = result.provider_message_id
                notif.sent_at = timezone.now()
                notif.attempt_count += 1
                notif.save()
                return True
            except (NotificationError, InvalidDeviceTokenError) as exc:
                notif.attempt_count += 1
                notif.failure_reason = str(exc)
                notif.save()
                return False

        elif notif.channel == NotificationChannel.SMS and notif.phone_number:
            try:
                provider = get_sms_provider()
                result = provider.send(SMSMessage(phone=notif.phone_number, text=notif.body))
                notif.status = NotificationStatus.SENT
                notif.provider_message_id = result.provider_message_id
                notif.sent_at = timezone.now()
                notif.attempt_count += 1
                notif.save()
                return True
            except NotificationError as exc:
                notif.attempt_count += 1
                notif.failure_reason = str(exc)
                notif.save()
                return False

        return False
