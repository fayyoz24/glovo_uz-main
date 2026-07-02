import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.reviews.constants import RATING_CHOICES, ReviewStatus, ReviewType


class Review(models.Model):
    """
    Buyurtma yetkazilgandan keyin mijoz tomonidan qoldirilgan baho.

    Bir buyurtma uchun bitta review (OneToOne order bilan).
    Review ichida merchant va courier uchun alohida ratinglar saqlanadi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="review",
        verbose_name="Buyurtma",
    )
    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="reviews",
        verbose_name="Mijoz",
    )

    # Do'kon bahosi
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.PROTECT,
        related_name="reviews",
        verbose_name="Do'kon",
    )
    merchant_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Do'kon bahosi (1–5)",
    )
    merchant_comment = models.TextField(
        blank=True,
        verbose_name="Do'kon haqida izoh",
    )

    # Kuryer bahosi (ixtiyoriy – COD yoki courier bo'lmagan hollarda null)
    courier = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courier_reviews",
        verbose_name="Kuryer",
    )
    courier_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Kuryer bahosi (1–5)",
    )
    courier_comment = models.TextField(
        blank=True,
        verbose_name="Kuryer haqida izoh",
    )

    # Umumiy holat
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.VISIBLE,
        db_index=True,
        verbose_name="Holat",
    )

    # Merchant javobi
    merchant_reply = models.TextField(
        blank=True,
        verbose_name="Do'kon javobi",
    )
    merchant_replied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Javob vaqti",
    )

    # Shikoyat
    flag_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Shikoyat soni",
    )
    flagged_by = models.ManyToManyField(
        "accounts.User",
        blank=True,
        related_name="flagged_reviews",
        verbose_name="Shikoyat qiluvchilar",
    )

    # Admin eslatmasi (moderatsiya)
    admin_note = models.TextField(
        blank=True,
        verbose_name="Admin eslatmasi",
    )
    moderated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_reviews",
        verbose_name="Moderator",
    )
    moderated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews"
        verbose_name = "Review"
        verbose_name_plural = "Reviewlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "status"]),
            models.Index(fields=["courier", "status"]),
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Review #{self.order_id} – {self.merchant_rating}⭐"
