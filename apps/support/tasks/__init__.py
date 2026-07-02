from __future__ import annotations

import logging
import uuid

from celery import shared_task
from django.utils import timezone

from apps.support.constants import ComplaintStatus, RefundRequestStatus
from apps.support.selectors import get_complaint_by_id, get_refund_request_by_id

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_support_new_complaint(self, complaint_id: str):
    """
    Notify the support team (e.g. via Telegram or email) when a new complaint
    is created. Triggered from create_complaint service.
    """
    from support.selectors import get_complaint_by_id

    complaint = get_complaint_by_id(complaint_id=uuid.UUID(complaint_id))
    if not complaint:
        logger.warning("notify_support_new_complaint: complaint %s not found", complaint_id)
        return

    try:
        # TODO: integrate with notifications app
        # from notifications.services import send_admin_telegram_alert
        # send_admin_telegram_alert(
        #     message=f"New complaint {complaint.public_id}: {complaint.subject}"
        # )
        logger.info(
            "Support notified for new complaint %s (type=%s)",
            complaint.public_id,
            complaint.complaint_type,
        )
    except Exception as exc:
        logger.error("notify_support_new_complaint failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_customer_complaint_updated(self, complaint_id: str, new_status: str):
    """
    Notify the customer via push/SMS when their complaint status changes.
    """
    from support.selectors import get_complaint_by_id

    complaint = get_complaint_by_id(complaint_id=uuid.UUID(complaint_id))
    if not complaint:
        return

    try:
        # TODO: integrate with notifications app
        # from notifications.services import send_push_notification
        # send_push_notification(
        #     user_id=complaint.customer_id,
        #     title="Your complaint has been updated",
        #     body=f"Complaint {complaint.public_id} is now: {new_status}",
        # )
        logger.info(
            "Customer %s notified about complaint %s -> %s",
            complaint.customer_id,
            complaint.public_id,
            new_status,
        )
    except Exception as exc:
        logger.error("notify_customer_complaint_updated failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def auto_close_resolved_complaints():
    """
    Periodic task (Celery Beat): auto-close complaints that have been in
    RESOLVED state for more than 72 hours without any customer response.
    Run daily via Celery Beat.
    """
    from support.models import Complaint

    cutoff = timezone.now() - timezone.timedelta(hours=72)
    qs = Complaint.objects.filter(
        status=ComplaintStatus.RESOLVED,
        resolved_at__lte=cutoff,
    )
    count = qs.update(
        status=ComplaintStatus.CLOSED,
        updated_at=timezone.now(),
    )
    logger.info("auto_close_resolved_complaints: closed %d complaints", count)
    return count


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def notify_customer_refund_reviewed(self, refund_id: str, action: str):
    """
    Notify customer when their refund request is approved or rejected.
    """
    refund = get_refund_request_by_id(refund_id=uuid.UUID(refund_id))
    if not refund:
        return

    try:
        status_label = "approved" if action == "approve" else "rejected"
        # TODO: integrate with notifications app
        # from notifications.services import send_push_notification
        # send_push_notification(
        #     user_id=refund.customer_id,
        #     title="Refund Request Update",
        #     body=f"Your refund request for order has been {status_label}.",
        # )
        logger.info(
            "Customer %s notified: refund %s was %s",
            refund.customer_id,
            refund_id,
            status_label,
        )
    except Exception as exc:
        logger.error("notify_customer_refund_reviewed failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def process_approved_refund(self, refund_id: str):
    """
    Trigger the payments app to process an approved refund.
    Called after approve_refund_request service.
    """
    refund = get_refund_request_by_id(refund_id=uuid.UUID(refund_id))
    if not refund:
        logger.warning("process_approved_refund: refund %s not found", refund_id)
        return

    if refund.status != RefundRequestStatus.APPROVED:
        logger.info(
            "process_approved_refund: refund %s is not in APPROVED state, skipping",
            refund_id,
        )
        return

    try:
        # TODO: integrate with payments app
        # from payments.services import create_refund_for_order
        # payment_refund = create_refund_for_order(
        #     order_id=refund.order_id,
        #     amount=refund.amount,
        #     reason=refund.reason,
        # )
        # from support.services import mark_refund_processed
        # mark_refund_processed(
        #     refund_request=refund,
        #     payment_refund_id=payment_refund.id,
        # )
        logger.info("process_approved_refund: triggered payment for refund %s", refund_id)
    except Exception as exc:
        logger.error("process_approved_refund failed for %s: %s", refund_id, exc)
        raise self.retry(exc=exc)
