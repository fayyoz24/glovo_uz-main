"""
Celery tasks for payments:
- Check pending transactions and expire them
- Send payment confirmation notifications
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expire_pending_transactions(self):
    """
    Expire Click/Payme transactions that have been pending for too long.
    Run every 15 minutes via Celery Beat.
    """
    from datetime import timedelta

    from apps.payments.models import PaymentProvider, PaymentStatus, PaymentTransaction

    cutoff = timezone.now() - timedelta(hours=1)  # 1 hour timeout

    expired = PaymentTransaction.objects.filter(
        provider__in=[PaymentProvider.CLICK, PaymentProvider.PAYME],
        status__in=[PaymentStatus.PENDING, PaymentStatus.WAITING],
        created_at__lt=cutoff,
    )

    count = expired.count()
    expired.update(status=PaymentStatus.CANCELLED, updated_at=timezone.now())

    if count:
        logger.info("Expired %d pending transactions", count)


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_payment_success_notification(self, order_id: str):
    """
    Send push/SMS notification after successful payment.
    Called by mark_order_paid.
    """
    try:
        from apps.notifications.services import notify_payment_success
        from apps.orders.models import Order

        order = Order.objects.select_related("customer").get(id=order_id)
        notify_payment_success(order)
        logger.info("Payment success notification sent for order %s", order_id)
    except Exception as exc:
        logger.error("send_payment_success_notification failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def reconcile_payme_transactions(from_ts: int = None, to_ts: int = None):
    """
    Fetch Payme statement and reconcile with local DB.
    Optional: run nightly via Celery Beat.
    """
    import requests
    import base64
    from django.conf import settings

    cfg_key = settings.PAYME_SECRET_KEY
    merchant_id = settings.PAYME_MERCHANT_ID
    auth = base64.b64encode(f"Paycom:{cfg_key}".encode()).decode()

    now = int(timezone.now().timestamp() * 1000)
    from_ts = from_ts or (now - 86400000)  # last 24h
    to_ts = to_ts or now

    try:
        resp = requests.post(
            "https://checkout.paycom.uz/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "GetStatement",
                "params": {"from": from_ts, "to": to_ts},
            },
            headers={"Authorization": f"Basic {auth}"},
            timeout=30,
        )
        data = resp.json()
        transactions = data.get("result", {}).get("transactions", [])
        logger.info("Payme reconciliation: %d transactions", len(transactions))
        # TODO: cross-check each with local DB and flag mismatches
    except Exception as e:
        logger.error("Payme reconciliation failed: %s", e)
