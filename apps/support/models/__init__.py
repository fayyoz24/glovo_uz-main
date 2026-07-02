import uuid
from django.db import models
from django.conf import settings

from apps.support.constants import (
    ComplaintStatus,
    ComplaintType,
    DisputeStatus,
    RefundRequestStatus,
    RefundReason,
    MessageSender,
    TicketPriority,
)


class Complaint(models.Model):
    """
    Customer complaint linked to an order.
    Support agents manage complaints through status transitions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=12, unique=True, editable=False)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="complaints",
    )
    # We reference order by ID to avoid circular imports; FK to orders.Order
    order_id = models.UUIDField(db_index=True)

    complaint_type = models.CharField(
        max_length=30,
        choices=ComplaintType.choices,
        default=ComplaintType.OTHER,
    )
    priority = models.CharField(
        max_length=10,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.OPEN,
    )

    subject = models.CharField(max_length=255)
    description = models.TextField()

    # Support agent assigned to this complaint
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_complaints",
    )

    # Internal note visible only to support team
    internal_note = models.TextField(blank=True, default="")
    resolution_note = models.TextField(blank=True, default="")

    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_complaint"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self):
        return f"Complaint {self.public_id} – {self.complaint_type} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = self._generate_public_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_public_id() -> str:
        import random
        import string
        return "SP-" + "".join(random.choices(string.digits, k=8))


class ComplaintMessage(models.Model):
    """
    Chat-like message thread on a complaint.
    Supports customer, support agent, and system messages.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_messages",
    )
    sender_type = models.CharField(
        max_length=10,
        choices=MessageSender.choices,
        default=MessageSender.CUSTOMER,
    )
    body = models.TextField()
    attachment = models.FileField(
        upload_to="support/attachments/",
        null=True,
        blank=True,
    )
    is_internal = models.BooleanField(
        default=False,
        help_text="If True, message is only visible to support agents.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_complaint_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["complaint", "created_at"]),
        ]

    def __str__(self):
        return f"Message on {self.complaint.public_id} by {self.sender_type}"


class Dispute(models.Model):
    """
    A formal dispute raised when a complaint is escalated
    or when there is a financial disagreement (e.g., payment not received).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.OneToOneField(
        Complaint,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dispute",
    )
    order_id = models.UUIDField(db_index=True)
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="disputes",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="handled_disputes",
    )

    status = models.CharField(
        max_length=30,
        choices=DisputeStatus.choices,
        default=DisputeStatus.PENDING,
    )
    description = models.TextField()
    resolution_note = models.TextField(blank=True, default="")

    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_dispute"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Dispute for order {self.order_id} ({self.status})"


class RefundRequest(models.Model):
    """
    Customer refund request. Can be linked to a complaint.
    Approved refunds are processed through the payments app.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.OneToOneField(
        Complaint,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="refund_request",
    )
    order_id = models.UUIDField(db_index=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="refund_requests",
    )

    reason = models.CharField(
        max_length=30,
        choices=RefundReason.choices,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Requested refund amount in UZS.",
    )
    status = models.CharField(
        max_length=20,
        choices=RefundRequestStatus.choices,
        default=RefundRequestStatus.PENDING,
    )

    # Set when admin approves/rejects
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_refund_requests",
    )
    review_note = models.TextField(blank=True, default="")

    # Set when payments app processes it
    payment_refund_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK to payments.Refund record after processing.",
    )

    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_refund_request"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Refund request {self.id} for order {self.order_id} ({self.status})"
