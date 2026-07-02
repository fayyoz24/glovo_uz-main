import uuid
from django.db import models


class CourierEarning(models.Model):
    """Har bir yetkazib berish uchun daromad yozuvi."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    courier = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="earnings",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="courier_earning",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    base_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tip = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "courier_earning"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Earning {self.courier} – {self.amount}"
