import uuid
from django.db import models
from apps.catalog.constants import ProductStatus


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        related_name="products",
    )
    branch = models.ForeignKey(
        "merchants.MerchantBranch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        help_text="If null, product belongs to all branches of the merchant",
    )
    category = models.ForeignKey(
        "catalog.ProductCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    name_uz = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    description_uz = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    # base_price stored in integer smallest unit (tiyin)
    base_price = models.PositiveIntegerField(help_text="Price in UZS tiyin (1 UZS = 100 tiyin)")
    sku = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True, help_text="Temporarily out of stock toggle")
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_product"
        indexes = [
            models.Index(fields=["merchant", "is_active", "is_available"]),
            models.Index(fields=["branch", "is_active", "is_available"]),
            models.Index(fields=["category"]),
        ]
        ordering = ["sort_order", "name_ru"]

    def __str__(self):
        return self.name_ru

    def get_name(self, lang: str = "ru") -> str:
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru

    @property
    def is_orderable(self) -> bool:
        return self.is_active and self.is_available and self.status == ProductStatus.ACTIVE


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="catalog/product_images/")
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catalog_product_image"
        ordering = ["sort_order"]

    def __str__(self):
        return f"Image for {self.product.name_ru}"
