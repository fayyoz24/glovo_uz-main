"""
apps/notifications/tasks.py

All notification tasks are async via Celery.
Services (orders, payments, dispatch etc.) call these tasks – never
the NotificationService directly from a request/response cycle.
"""
from __future__ import annotations

import logging
import uuid

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Helper to resolve user phone & email from accounts app              #
# ------------------------------------------------------------------ #

def _get_user_contact_info(user_id) -> tuple[str | None, str | None, str]:
    """Returns (phone, email, lang) for user."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        phone = getattr(user, "phone", None)
        email = getattr(user, "email", None)
        lang = getattr(user, "language", "uz") or "uz"
        return phone, email, lang
    except Exception:
        return None, None, "uz"


# ================================================================== #
#  Event tasks – called by other apps (orders, payments, dispatch)    #
# ================================================================== #

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="notifications.send_order_created",
)
def send_order_created(self, order_id: str, customer_id, context: dict) -> None:
    from apps.notifications.services import NotificationService
    from apps.notifications.constants import NotificationEvent

    try:
        phone, email, lang = _get_user_contact_info(customer_id)
        NotificationService.send_event(
            event=NotificationEvent.ORDER_CREATED,
            recipient_id=customer_id,
            context=context,
            order_id=uuid.UUID(order_id),
            phone=phone,
            email=email,
            lang=lang,
        )
    except Exception as exc:
        logger.exception("send_order_created failed for order %s", order_id)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="notifications.send_order_status_changed",
)
def send_order_status_changed(
    self,
    order_id: str,
    customer_id,
    event: str,
    context: dict,
) -> None:
    from apps.notifications.services import NotificationService

    try:
        phone, email, lang = _get_user_contact_info(customer_id)
        NotificationService.send_event(
            event=event,
            recipient_id=customer_id,
            context=context,
            order_id=uuid.UUID(order_id),
            phone=phone,
            lang=lang,
        )
    except Exception as exc:
        logger.exception(
            "send_order_status_changed failed: order=%s event=%s", order_id, event
        )
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="notifications.send_merchant_new_order",
)
def send_merchant_new_order(
    self,
    order_id: str,
    merchant_owner_id,
    context: dict,
    telegram_chat_id: str | None = None,
) -> None:
    from apps.notifications.services import NotificationService
    from apps.notifications.constants import NotificationEvent

    try:
        phone, email, lang = _get_user_contact_info(merchant_owner_id)
        NotificationService.send_event(
            event=NotificationEvent.MERCHANT_NEW_ORDER,
            recipient_id=merchant_owner_id,
            context=context,
            order_id=uuid.UUID(order_id),
            phone=phone,
            telegram_chat_id=telegram_chat_id,
            lang=lang,
        )
    except Exception as exc:
        logger.exception("send_merchant_new_order failed for order %s", order_id)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="notifications.send_courier_order_offer",
)
def send_courier_order_offer(
    self,
    order_id: str,
    courier_user_id,
    context: dict,
) -> None:
    from apps.notifications.services import NotificationService
    from apps.notifications.constants import NotificationEvent

    try:
        phone, email, lang = _get_user_contact_info(courier_user_id)
        NotificationService.send_event(
            event=NotificationEvent.COURIER_NEW_ORDER_OFFER,
            recipient_id=courier_user_id,
            context=context,
            order_id=uuid.UUID(order_id),
            phone=phone,
            lang=lang,
        )
    except Exception as exc:
        logger.exception(
            "send_courier_order_offer failed: order=%s courier=%s", order_id, courier_user_id
        )
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="notifications.send_payment_notification",
)
def send_payment_notification(
    self,
    event: str,
    customer_id,
    context: dict,
    order_id: str | None = None,
) -> None:
    from apps.notifications.services import NotificationService

    try:
        phone, email, lang = _get_user_contact_info(customer_id)
        NotificationService.send_event(
            event=event,
            recipient_id=customer_id,
            context=context,
            order_id=uuid.UUID(order_id) if order_id else None,
            phone=phone,
            email=email,
            lang=lang,
        )
    except Exception as exc:
        logger.exception("send_payment_notification failed: event=%s", event)
        raise self.retry(exc=exc)


@shared_task(name="notifications.retry_failed_notifications")
def retry_failed_notifications() -> dict:
    """
    Periodic task: retry failed retriable notifications.
    Schedule: every 10 minutes via Celery Beat.
    """
    from apps.notifications.selectors import get_failed_retriable_notifications
    from apps.notifications.services import NotificationService

    notifications = get_failed_retriable_notifications(limit=200)
    sent = 0
    still_failed = 0

    for notif in notifications:
        success = NotificationService.retry_notification(notif)
        if success:
            sent += 1
        else:
            still_failed += 1

    logger.info(
        "retry_failed_notifications: sent=%d, still_failed=%d", sent, still_failed
    )
    return {"sent": sent, "still_failed": still_failed}


@shared_task(name="notifications.cleanup_old_notifications")
def cleanup_old_notifications(days: int = 90) -> dict:
    """
    Periodic task: delete read in-app notifications older than `days` days.
    Schedule: daily via Celery Beat.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.notifications.models import Notification
    from apps.notifications.constants import NotificationChannel

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = Notification.objects.filter(
        channel=NotificationChannel.IN_APP,
        read_at__isnull=False,
        created_at__lt=cutoff,
    ).delete()

    logger.info("cleanup_old_notifications: deleted=%d", deleted)
    return {"deleted": deleted}


