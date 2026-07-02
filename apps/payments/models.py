import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentProvider(models.TextChoices):
    CLICK = "click", _("Click")
    PAYME = "payme", _("Payme")
    CASH = "cash", _("Cash on Delivery")


class PaymentStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    WAITING = "waiting", _("Waiting")       # Click: waiting for confirmation
    PAID = "paid", _("Paid")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")
    REFUNDED = "refunded", _("Refunded")
    PARTIALLY_REFUNDED = "partially_refunded", _("Partially Refunded")


class RefundStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")
    PROCESSED = "processed", _("Processed")


class PaymentTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("Order"),
    )

    # Provider info
    provider = models.CharField(
        max_length=20,
        choices=PaymentProvider.choices,
        verbose_name=_("Provider"),
    )
    provider_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Provider Transaction ID"),
    )

    # Amount
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Amount"),
    )
    currency = models.CharField(
        max_length=3,
        default="UZS",
        verbose_name=_("Currency"),
    )

    # Status
    status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )

    # Provider-specific fields
    # Click: merchant_trans_id, sign_time, etc.
    # Payme: _id (ObjectId), time, perform_time, etc.
    raw_request = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("Raw Request"),
    )
    raw_response = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("Raw Response"),
    )

    # For Payme: stores the payme transaction id and state
    extra = models.JSONField(
        blank=True,
        default=dict,
        verbose_name=_("Extra Data"),
    )

    # URL returned to customer to complete payment
    payment_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Payment URL"),
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Payment Transaction")
        verbose_name_plural = _("Payment Transactions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["provider", "provider_transaction_id"]),
        ]

    def __str__(self):
        return f"{self.provider} | {self.order_id} | {self.status}"

    @property
    def is_paid(self):
        return self.status == PaymentStatus.PAID

    @property
    def amount_tiyin(self):
        """Amount in tiyin (Payme uses tiyin — 1 UZS = 100 tiyin)."""
        return int(self.amount * 100)


class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="refunds",
        verbose_name=_("Order"),
    )
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.PROTECT,
        related_name="refunds",
        verbose_name=_("Transaction"),
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Refund Amount"),
    )
    reason = models.TextField(verbose_name=_("Reason"))

    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )

    # Provider response on refund
    provider_response = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Refund")
        verbose_name_plural = _("Refunds")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.id} | Order {self.order_id} | {self.status}"
