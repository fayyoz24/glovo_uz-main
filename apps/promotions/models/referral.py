import uuid

from django.db import models


class ReferralCode(models.Model):
    """
    Har bir foydalanuvchiga bitta referal kod beriladi.
    Do'st shu kod orqali ro'yxatdan o'tganda ikkalasiga bonus beriladi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="referral_code",
        verbose_name="Egasi",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Referal kod",
    )

    # Referrerga beriladigan bonus (so'm yoki %)
    referrer_bonus_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Referrerga bonus (so'm)",
    )
    # Yangi ro'yxatdan o'tuvchiga beriladigan bonus
    referee_bonus_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Yangi foydalanuvchiga bonus (so'm)",
    )

    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maksimal foydalanish soni",
    )
    use_count = models.PositiveIntegerField(default=0, verbose_name="Foydalanish soni")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referral_codes"
        verbose_name = "Referal kod"
        verbose_name_plural = "Referal kodlar"

    def __str__(self):
        return f"{self.code} ({self.user})"


class ReferralUsage(models.Model):
    """
    Referal koddan foydalanish tarixi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    referral_code = models.ForeignKey(
        ReferralCode,
        on_delete=models.PROTECT,
        related_name="usages",
        verbose_name="Referal kod",
    )
    referee = models.OneToOneField(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="referral_usage",
        verbose_name="Yangi foydalanuvchi",
    )

    referrer_bonus_credited = models.BooleanField(default=False)
    referee_bonus_credited = models.BooleanField(default=False)

    used_at = models.DateTimeField(auto_now_add=True)
    first_order_placed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Birinchi buyurtma vaqti",
        help_text="Bonus shu vaqtda beriladi",
    )

    class Meta:
        db_table = "referral_usages"
        verbose_name = "Referal foydalanish"
        verbose_name_plural = "Referal foydalanishlar"

    def __str__(self):
        return f"{self.referral_code.code} → {self.referee}"
