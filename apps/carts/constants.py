from django.db import models


class CartStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    ORDERED = "ordered", "Buyurtma berilgan"
    EXPIRED = "expired", "Muddati o'tgan"
    CLEARED = "cleared", "Tozalangan"

CART_EXPIRY_HOURS = 24
MAX_CART_ITEM_QTY = 50
