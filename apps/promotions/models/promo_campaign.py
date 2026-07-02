import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.promotions.constants import DiscountType, PromoStatus, PromoTargetType


class PromoCampaign(models.Model):
    """
    Promo kampaniya modeli.
    Discount type: percentage | fixed | free_delivery
    Target: all | new_users | specific_users | merchant
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=200, verbose_name="Kampaniya nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Promo kod",
        help_text="Mijoz kiritadigan kod, masalan: YOZSALE20",
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name="Chegirma turi",
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Chegirma qiymati",
        help_text="Foiz yoki so'm miqdori",
    )
    max_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Maksimal chegirma (so'm)",
        help_text="Foiz chegirmalar uchun yuqori chegara",
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Minimal buyurtma summasi",
    )

    # Foydalanish limiti
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Umumiy foydalanish limiti",
        help_text="Null = cheksiz",
    )
    per_user_limit = models.PositiveIntegerField(
        default=1,
        verbose_name="Bir foydalanuvchi uchun limit",
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Hozirgi foydalanish soni",
    )

    # Vaqt oralig'i
    starts_at = models.DateTimeField(verbose_name="Boshlanish vaqti")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Tugash vaqti")

    # Target auditoriya
    target_type = models.CharField(
        max_length=20,
        choices=PromoTargetType.choices,
        default=PromoTargetType.ALL,
        verbose_name="Maqsadli auditoriya",
    )
    # Faqat target_type=MERCHANT bo'lganda
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promo_campaigns",
        verbose_name="Do'kon",
    )
    # Faqat target_type=SPECIFIC_USERS bo'lganda
    allowed_users = models.ManyToManyField(
        "accounts.User",
        blank=True,
        related_name="allowed_promo_campaigns",
        verbose_name="Ruxsat etilgan foydalanuvchilar",
    )

    status = models.CharField(
        max_length=20,
        choices=PromoStatus.choices,
        default=PromoStatus.DRAFT,
        db_index=True,
        verbose_name="Holat",
    )

    is_combinable = models.BooleanField(
        default=False,
        verbose_name="Boshqa promo bilan birlashtirish mumkinmi?",
    )
    applies_to_delivery_fee = models.BooleanField(
        default=False,
        verbose_name="Yetkazish narxiga ham qo'llansinmi?",
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_promo_campaigns",
        verbose_name="Yaratuvchi admin",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "promo_campaigns"
        verbose_name = "Promo kampaniya"
        verbose_name_plural = "Promo kampaniyalar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["status", "starts_at", "ends_at"]),
        ]

    def __str__(self):
        return f"{self.code} – {self.name}"

    # -------------------------------------------------------------------------
    # Helper properties (biznes logikal service'da, bu yerda faqat oddiy check)
    # -------------------------------------------------------------------------

    @property
    def is_time_valid(self) -> bool:
        now = timezone.now()
        if now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    @property
    def is_usage_available(self) -> bool:
        if self.usage_limit is None:
            return True
        return self.usage_count < self.usage_limit

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        """
        Chegirma miqdorini hisoblaydi.
        Biznes logikaning qismi – service'da ham chaqirilishi mumkin.
        """
        if self.discount_type == DiscountType.PERCENTAGE:
            discount = subtotal * (self.discount_value / Decimal("100"))
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        elif self.discount_type == DiscountType.FIXED:
            return min(self.discount_value, subtotal)
        elif self.discount_type == DiscountType.FREE_DELIVERY:
            return Decimal("0.00")  # Yetkazish narxi alohida tushiriladi
        return Decimal("0.00")
