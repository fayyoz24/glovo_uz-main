import uuid
from django.db import models
from apps.catalog.constants import ModifierGroupType


class ProductModifierGroup(models.Model):
    """
    Modifier guruh — masalan: "Qo'shimcha sous tanlang", "Pishirish darajasi".
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="modifier_groups",
    )
    name_uz = models.CharField(max_length=150)
    name_ru = models.CharField(max_length=150)
    group_type = models.CharField(
        max_length=10,
        choices=ModifierGroupType.choices,
        default=ModifierGroupType.MULTIPLE,
    )
    min_select = models.PositiveSmallIntegerField(default=0)
    max_select = models.PositiveSmallIntegerField(default=1)
    required = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_modifier_group"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.product.name_ru} – {self.name_ru}"

    def get_name(self, lang: str = "ru") -> str:
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru


class ProductModifierOption(models.Model):
    """
    Modifier option — masalan: "Ketchup (+0)", "Qo'shimcha pishloq (+5000)".
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        ProductModifierGroup,
        on_delete=models.CASCADE,
        related_name="options",
    )
    name_uz = models.CharField(max_length=150)
    name_ru = models.CharField(max_length=150)
    price_delta = models.PositiveIntegerField(
        default=0,
        help_text="Additional price in tiyin",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "catalog_modifier_option"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.group.name_ru} – {self.name_ru}"

    def get_name(self, lang: str = "ru") -> str:
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru
