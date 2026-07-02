import uuid

from django.db import models


class FlagReason(models.TextChoices):
    SPAM = "spam", "Spam"
    OFFENSIVE = "offensive", "Haqoratli so'zlar"
    IRRELEVANT = "irrelevant", "Buyurtmaga aloqasi yo'q"
    FAKE = "fake", "Soxta review"
    OTHER = "other", "Boshqa"


class ReviewFlag(models.Model):
    """
    Foydalanuvchi reviewni shikoyat qilganda yaratiladi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        related_name="flags",
        verbose_name="Review",
    )
    flagged_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="review_flags",
        verbose_name="Shikoyat qiluvchi",
    )
    reason = models.CharField(
        max_length=20,
        choices=FlagReason.choices,
        default=FlagReason.OTHER,
        verbose_name="Sabab",
    )
    note = models.TextField(blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review_flags"
        verbose_name = "Review shikoyati"
        verbose_name_plural = "Review shikoyatlari"
        unique_together = [("review", "flagged_by")]

    def __str__(self):
        return f"Flag: {self.review_id} by {self.flagged_by_id}"
