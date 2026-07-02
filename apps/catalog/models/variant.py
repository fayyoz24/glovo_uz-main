import uuid
from django.db import models


class ProductVariant(models.Model):
    """
    Product variants — masalan: kichik/o'rta/katta pizza.
    Variant narxi = product.base_price + price_delta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="variants",
    )
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    # Delta can be negative (discount variant)
    price_delta = models.IntegerField(
        default=0,
        help_text="Amount added to base_price in tiyin. Can be negative.",
    )
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "catalog_product_variant"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.product.name_ru} – {self.name_ru}"

    @property
    def final_price(self) -> int:
        return self.product.base_price + self.price_delta

    def get_name(self, lang: str = "ru") -> str:
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru
