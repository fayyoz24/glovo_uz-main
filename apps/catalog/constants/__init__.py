from django.db import models


class ProductStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    INACTIVE = "inactive", "Nofaol"
    OUT_OF_STOCK = "out_of_stock", "Mavjud emas"

class ModifierGroupType(models.TextChoices):
    SINGLE = "single", "Bitta tanlash"
    MULTIPLE = "multiple", "Ko'p tanlash"

class ProductStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

    CHOICES = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
        (OUT_OF_STOCK, "Out of Stock"),
    ]


class UnitType:
    """Mahsulot qanday o'lchovda sotilishini bildiradi — do'kon egasi mahsulot
    qo'shishda tanlaydi. Dona (piece) uchun butun sonli miqdor, kg uchun
    kasrli (0.1/0.5 kg) miqdor bilan savatga qo'shish mumkin."""
    PIECE = "piece"
    KG = "kg"

    CHOICES = [
        (PIECE, "Dona"),
        (KG, "Kilogramm"),
    ]


class ModifierGroupType:
    SINGLE = "single"    # radio — faqat 1 ta tanlash
    MULTI = "multi"      # checkbox — bir nechta tanlash

    CHOICES = [
        (SINGLE, "Single Choice"),
        (MULTI, "Multiple Choice"),
    ]
