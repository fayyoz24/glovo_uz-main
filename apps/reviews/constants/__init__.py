from django.db import models


class ReviewType(models.TextChoices):
    MERCHANT = "merchant", "Do'kon"
    COURIER = "courier", "Kuryer"
    ORDER = "order", "Buyurtma"


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Moderatsiyada"
    VISIBLE = "visible", "Ko'rinadigan"
    HIDDEN = "hidden", "Yashirilgan"
    FLAGGED = "flagged", "Shikoyat qilingan"


RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
