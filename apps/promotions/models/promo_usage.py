import uuid

from django.db import models


class PromoUsage(models.Model):
    """
    Promo koddan foydalanish tarixi.
    Har bir order uchun bitta yozuv.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    promo = models.ForeignKey(
        "promotions.PromoCampaign",
        on_delete=models.PROTECT,
        related_name="usages",
        verbose_name="Promo kampaniya",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="promo_usages",
        verbose_name="Foydalanuvchi",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="promo_usage",
        verbose_name="Buyurtma",
    )

    discount_amount_applied = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Qo'llanilgan chegirma (so'm)",
    )
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="Ishlatilgan vaqt")

    class Meta:
        db_table = "promo_usages"
        verbose_name = "Promo foydalanish"
        verbose_name_plural = "Promo foydalanishlar"
        indexes = [
            models.Index(fields=["promo", "user"]),
            models.Index(fields=["user", "used_at"]),
        ]

    def __str__(self):
        return f"{self.promo.code} → {self.user} (order: {self.order_id})"
