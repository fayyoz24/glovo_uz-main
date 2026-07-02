import uuid
from django.db import models
from apps.orders.constants import OrderStatus, PaymentMethod, PaymentStatus


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, editable=False)

    # Tomonlar
    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    branch = models.ForeignKey(
        "merchants.MerchantBranch",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    courier = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="courier_orders",
    )

    # Manzil snapshot (buyurtma paytidagi nusxa)
    address_snapshot = models.JSONField(default=dict)

    # Holat
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    # To'lov
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    # Narxlar (snapshot)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="UZS")

    # Bekor qilish
    cancel_reason = models.CharField(max_length=50, blank=True)
    cancel_note = models.CharField(max_length=512, blank=True)

    # Vaqtlar
    placed_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order"
        ordering = ["-placed_at"]
        indexes = [
            models.Index(fields=["customer", "placed_at"]),
            models.Index(fields=["branch", "status"]),
            models.Index(fields=["courier", "status"]),
            models.Index(fields=["public_id"]),
        ]

    def __str__(self):
        return f"Order #{self.public_id} – {self.status}"

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = self._generate_public_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_public_id() -> str:
        import random
        import string
        return "GL" + "".join(random.choices(string.digits, k=8))
