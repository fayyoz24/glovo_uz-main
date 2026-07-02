import uuid

from django.db import models


class ReviewImage(models.Model):
    """
    Mijoz review bilan birga rasm yuklashi mumkin.
    Masalan, noto'g'ri yetkazilgan mahsulot rasmi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Review",
    )
    image = models.ImageField(
        upload_to="reviews/images/%Y/%m/",
        verbose_name="Rasm",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review_images"
        verbose_name = "Review rasmi"
        verbose_name_plural = "Review rasmlari"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"Image for review {self.review_id}"
