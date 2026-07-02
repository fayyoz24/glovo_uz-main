from django.db import models


class ProductStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    INACTIVE = "inactive", "Nofaol"
    OUT_OF_STOCK = "out_of_stock", "Mavjud emas"

class ModifierGroupType(models.TextChoices):
    SINGLE = "single", "Bitta tanlash"
    MULTIPLE = "multiple", "Ko'p tanlash"
