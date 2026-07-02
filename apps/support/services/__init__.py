from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone

from apps.support.models import Complaint, ComplaintMessage, Dispute, RefundRequest
from apps.support.constants import (
    ComplaintStatus,
    DisputeStatus,
    MessageSender,
    RefundRequestStatus,
    TicketPriority,
)
from apps.support.exceptions import (
    ComplaintAlreadyClosed,
    DuplicateComplaint,
    InvalidStatusTransition,
    RefundAlreadyProcessed,
)
from apps.support.selectors import (
    get_open_complaint_for_order,
    get_existing_refund_for_order,
)

# Valid status transitions for complaints
COMPLAINT_TRANSITIONS: dict[str, list[str]] = {
    ComplaintStatus.OPEN: [
        ComplaintStatus.IN_REVIEW,
        ComplaintStatus.CLOSED,
        ComplaintStatus.REJECTED,
    ],
    ComplaintStatus.IN_REVIEW: [
        ComplaintStatus.PENDING_USER,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.REJECTED,
        ComplaintStatus.CLOSED,
    ],
    ComplaintStatus.PENDING_USER: [
        ComplaintStatus.IN_REVIEW,
        ComplaintStatus.CLOSED,
    ],
    ComplaintStatus.RESOLVED: [ComplaintStatus.CLOSED],
    ComplaintStatus.CLOSED: [],
    ComplaintStatus.REJECTED: [],
}


# ---------------------------------------------------------------------------
# Complaint services
# ---------------------------------------------------------------------------


@transaction.atomic
def create_complaint(
    *,
    customer_id: int,
    order_id: uuid.UUID,
    complaint_type: str,
    subject: str,
    description: str,
    priority: str = TicketPriority.MEDIUM,
) -> Complaint:
    """
    Create a new complaint for an order.
    Raises DuplicateComplaint if an active complaint already exists for this order.
    """
    existing = get_open_complaint_for_order(order_id=order_id, user_id=customer_id)
    if existing:
        raise DuplicateComplaint()

    complaint = Complaint.objects.create(
        customer_id=customer_id,
        order_id=order_id,
        complaint_type=complaint_type,
        subject=subject,
        description=description,
        priority=priority,
        status=ComplaintStatus.OPEN,
    )

    # Auto-add system message
    ComplaintMessage.objects.create(
        complaint=complaint,
        sender=None,
        sender_type=MessageSender.SYSTEM,
        body="Your complaint has been received. Our support team will review it shortly.",
        is_internal=False,
    )

    return complaint


@transaction.atomic
def update_complaint_status(
    *,
    complaint: Complaint,
    new_status: str,
    agent_id: Optional[int] = None,
    note: str = "",
) -> Complaint:
    """
    Transition complaint to a new status.
    Validates the transition against allowed states.
    """
    allowed = COMPLAINT_TRANSITIONS.get(complaint.status, [])
    if new_status not in allowed:
        raise InvalidStatusTransition(
            detail=f"Cannot transition from '{complaint.status}' to '{new_status}'."
        )

    complaint.status = new_status
    if note:
        complaint.resolution_note = note
    if new_status in (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED):
        complaint.resolved_at = timezone.now()

    complaint.save(update_fields=["status", "resolution_note", "resolved_at", "updated_at"])

    # Add a system message for the transition
    ComplaintMessage.objects.create(
        complaint=complaint,
        sender_id=agent_id,
        sender_type=MessageSender.SUPPORT if agent_id else MessageSender.SYSTEM,
        body=f"Complaint status updated to: {new_status}." + (f" Note: {note}" if note else ""),
        is_internal=False,
    )

    return complaint


@transaction.atomic
def assign_complaint(
    *,
    complaint: Complaint,
    agent_id: int,
    note: str = "",
) -> Complaint:
    """Assign a complaint to a support agent."""
    complaint.assigned_to_id = agent_id
    if complaint.status == ComplaintStatus.OPEN:
        complaint.status = ComplaintStatus.IN_REVIEW
    complaint.save(update_fields=["assigned_to_id", "status", "updated_at"])

    ComplaintMessage.objects.create(
        complaint=complaint,
        sender_id=agent_id,
        sender_type=MessageSender.SYSTEM,
        body=f"Complaint assigned to support agent.",
        is_internal=True,
    )
    return complaint


def add_complaint_message(
    *,
    complaint: Complaint,
    sender_id: Optional[int],
    sender_type: str,
    body: str,
    is_internal: bool = False,
    attachment=None,
) -> ComplaintMessage:
    """Add a message to a complaint thread."""
    if complaint.status in (ComplaintStatus.CLOSED, ComplaintStatus.REJECTED):
        raise ComplaintAlreadyClosed()

    message = ComplaintMessage.objects.create(
        complaint=complaint,
        sender_id=sender_id,
        sender_type=sender_type,
        body=body,
        is_internal=is_internal,
        attachment=attachment,
    )

    # If customer replies while PENDING_USER, move back to IN_REVIEW
    if (
        sender_type == MessageSender.CUSTOMER
        and complaint.status == ComplaintStatus.PENDING_USER
    ):
        complaint.status = ComplaintStatus.IN_REVIEW
        complaint.save(update_fields=["status", "updated_at"])

    return message


# ---------------------------------------------------------------------------
# Dispute services
# ---------------------------------------------------------------------------


@transaction.atomic
def create_dispute(
    *,
    order_id: uuid.UUID,
    raised_by_id: int,
    description: str,
    complaint_id: Optional[uuid.UUID] = None,
) -> Dispute:
    dispute = Dispute.objects.create(
        order_id=order_id,
        raised_by_id=raised_by_id,
        description=description,
        complaint_id=complaint_id,
        status=DisputeStatus.PENDING,
    )
    return dispute


@transaction.atomic
def update_dispute_status(
    *,
    dispute: Dispute,
    new_status: str,
    agent_id: Optional[int] = None,
    resolution_note: str = "",
) -> Dispute:
    dispute.status = new_status
    if resolution_note:
        dispute.resolution_note = resolution_note
    if new_status in (
        DisputeStatus.RESOLVED_REFUND,
        DisputeStatus.RESOLVED_NO_REFUND,
        DisputeStatus.CLOSED,
    ):
        dispute.resolved_at = timezone.now()
    if agent_id:
        dispute.assigned_to_id = agent_id
    dispute.save(
        update_fields=[
            "status",
            "resolution_note",
            "resolved_at",
            "assigned_to_id",
            "updated_at",
        ]
    )
    return dispute


# ---------------------------------------------------------------------------
# RefundRequest services
# ---------------------------------------------------------------------------


@transaction.atomic
def create_refund_request(
    *,
    order_id: uuid.UUID,
    customer_id: int,
    reason: str,
    amount: Decimal,
    complaint_id: Optional[uuid.UUID] = None,
) -> RefundRequest:
    """
    Create a refund request.
    Raises exception if a non-cancelled refund request already exists for the order.
    """
    existing = get_existing_refund_for_order(order_id=order_id)
    if existing:
        raise RefundAlreadyProcessed(
            detail="A refund request already exists for this order."
        )

    return RefundRequest.objects.create(
        order_id=order_id,
        customer_id=customer_id,
        reason=reason,
        amount=amount,
        complaint_id=complaint_id,
        status=RefundRequestStatus.PENDING,
    )


@transaction.atomic
def approve_refund_request(
    *,
    refund_request: RefundRequest,
    reviewed_by_id: int,
    review_note: str = "",
) -> RefundRequest:
    if refund_request.status != RefundRequestStatus.PENDING:
        raise RefundAlreadyProcessed()

    refund_request.status = RefundRequestStatus.APPROVED
    refund_request.reviewed_by_id = reviewed_by_id
    refund_request.review_note = review_note
    refund_request.save(
        update_fields=["status", "reviewed_by_id", "review_note", "updated_at"]
    )
    return refund_request


@transaction.atomic
def reject_refund_request(
    *,
    refund_request: RefundRequest,
    reviewed_by_id: int,
    review_note: str = "",
) -> RefundRequest:
    if refund_request.status != RefundRequestStatus.PENDING:
        raise RefundAlreadyProcessed()

    refund_request.status = RefundRequestStatus.REJECTED
    refund_request.reviewed_by_id = reviewed_by_id
    refund_request.review_note = review_note
    refund_request.save(
        update_fields=["status", "reviewed_by_id", "review_note", "updated_at"]
    )
    return refund_request


@transaction.atomic
def mark_refund_processed(
    *,
    refund_request: RefundRequest,
    payment_refund_id: uuid.UUID,
) -> RefundRequest:
    """Called by payments app after Refund record is created."""
    if refund_request.status != RefundRequestStatus.APPROVED:
        raise InvalidStatusTransition(
            detail="Only approved refund requests can be marked as processed."
        )
    refund_request.status = RefundRequestStatus.PROCESSED
    refund_request.payment_refund_id = payment_refund_id
    refund_request.processed_at = timezone.now()
    refund_request.save(
        update_fields=["status", "payment_refund_id", "processed_at", "updated_at"]
    )
    return refund_request
