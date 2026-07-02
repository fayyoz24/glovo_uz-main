from django.db import models


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "Foiz (%)"
    FIXED = "fixed", "Belgilangan summa"
    FREE_DELIVERY = "free_delivery", "Tekin yetkazish"


class PromoStatus(models.TextChoices):
    DRAFT = "draft", "Qoralama"
    ACTIVE = "active", "Faol"
    PAUSED = "paused", "To'xtatilgan"
    EXPIRED = "expired", "Muddati tugagan"
    EXHAUSTED = "exhausted", "Limiti tugagan"


class PromoTargetType(models.TextChoices):
    ALL = "all", "Hamma"
    NEW_USERS = "new_users", "Yangi foydalanuvchilar"
    SPECIFIC_USERS = "specific_users", "Tanlangan foydalanuvchilar"
    MERCHANT = "merchant", "Muayyan do'kon"
