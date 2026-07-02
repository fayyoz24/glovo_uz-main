from __future__ import annotations

import uuid
from typing import Optional

from django.db.models import QuerySet, Prefetch

from apps.support.models import Complaint, ComplaintMessage, Dispute, RefundRequest
from apps.support.constants import ComplaintStatus, DisputeStatus, RefundRequestStatus


# ---------------------------------------------------------------------------
# Complaint selectors
# ---------------------------------------------------------------------------


def get_complaint_by_id(complaint_id: uuid.UUID) -> Optional[Complaint]:
    try:
        return Complaint.objects.select_related(
            "customer", "assigned_to"
        ).get(id=complaint_id)
    except Complaint.DoesNotExist:
        return None


def get_complaint_by_public_id(public_id: str) -> Optional[Complaint]:
    try:
        return Complaint.objects.select_related(
            "customer", "assigned_to"
        ).get(public_id=public_id)
    except Complaint.DoesNotExist:
        return None


def get_complaints_for_customer(
    user_id: int,
    status: Optional[str] = None,
) -> QuerySet[Complaint]:
    qs = Complaint.objects.filter(customer_id=user_id).select_related(
        "customer", "assigned_to"
    )
    if status:
        qs = qs.filter(status=status)
    return qs


def get_complaints_for_order(order_id: uuid.UUID) -> QuerySet[Complaint]:
    return Complaint.objects.filter(order_id=order_id).select_related(
        "customer", "assigned_to"
    )


def get_open_complaint_for_order(order_id: uuid.UUID, user_id: int) -> Optional[Complaint]:
    return Complaint.objects.filter(
        order_id=order_id,
        customer_id=user_id,
        status__in=[
            ComplaintStatus.OPEN,
            ComplaintStatus.IN_REVIEW,
            ComplaintStatus.PENDING_USER,
        ],
    ).first()


def get_all_complaints(
    status: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    priority: Optional[str] = None,
) -> QuerySet[Complaint]:
    qs = Complaint.objects.select_related("customer", "assigned_to").all()
    if status:
        qs = qs.filter(status=status)
    if assigned_to_id:
        qs = qs.filter(assigned_to_id=assigned_to_id)
    if priority:
        qs = qs.filter(priority=priority)
    return qs


def get_complaint_with_messages(complaint_id: uuid.UUID) -> Optional[Complaint]:
    messages_qs = ComplaintMessage.objects.select_related("sender").order_by("created_at")
    try:
        return Complaint.objects.prefetch_related(
            Prefetch("messages", queryset=messages_qs)
        ).select_related("customer", "assigned_to").get(id=complaint_id)
    except Complaint.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# ComplaintMessage selectors
# ---------------------------------------------------------------------------


def get_messages_for_complaint(
    complaint_id: uuid.UUID,
    include_internal: bool = False,
) -> QuerySet[ComplaintMessage]:
    qs = ComplaintMessage.objects.filter(complaint_id=complaint_id).select_related("sender")
    if not include_internal:
        qs = qs.filter(is_internal=False)
    return qs


# ---------------------------------------------------------------------------
# Dispute selectors
# ---------------------------------------------------------------------------


def get_dispute_by_id(dispute_id: uuid.UUID) -> Optional[Dispute]:
    try:
        return Dispute.objects.select_related(
            "raised_by", "assigned_to", "complaint"
        ).get(id=dispute_id)
    except Dispute.DoesNotExist:
        return None


def get_disputes_for_order(order_id: uuid.UUID) -> QuerySet[Dispute]:
    return Dispute.objects.filter(order_id=order_id).select_related(
        "raised_by", "assigned_to"
    )


def get_all_disputes(
    status: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
) -> QuerySet[Dispute]:
    qs = Dispute.objects.select_related("raised_by", "assigned_to", "complaint").all()
    if status:
        qs = qs.filter(status=status)
    if assigned_to_id:
        qs = qs.filter(assigned_to_id=assigned_to_id)
    return qs


# ---------------------------------------------------------------------------
# RefundRequest selectors
# ---------------------------------------------------------------------------


def get_refund_request_by_id(refund_id: uuid.UUID) -> Optional[RefundRequest]:
    try:
        return RefundRequest.objects.select_related(
            "customer", "reviewed_by", "complaint"
        ).get(id=refund_id)
    except RefundRequest.DoesNotExist:
        return None


def get_refund_requests_for_customer(
    user_id: int,
    status: Optional[str] = None,
) -> QuerySet[RefundRequest]:
    qs = RefundRequest.objects.filter(customer_id=user_id).select_related(
        "customer", "reviewed_by"
    )
    if status:
        qs = qs.filter(status=status)
    return qs


def get_all_refund_requests(
    status: Optional[str] = None,
) -> QuerySet[RefundRequest]:
    qs = RefundRequest.objects.select_related(
        "customer", "reviewed_by", "complaint"
    ).all()
    if status:
        qs = qs.filter(status=status)
    return qs


def get_existing_refund_for_order(order_id: uuid.UUID) -> Optional[RefundRequest]:
    return RefundRequest.objects.filter(
        order_id=order_id,
        status__in=[
            RefundRequestStatus.PENDING,
            RefundRequestStatus.APPROVED,
            RefundRequestStatus.PROCESSED,
        ],
    ).first()
