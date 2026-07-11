import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.catalog.constants import ProductStatus
from apps.catalog.validators import validate_product_image_size
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from apps.catalog.utils.util import product_image_upload_path
import os

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
    name_ru = models.CharField(max_length=200, blank=True, null=True)
    name_en = models.CharField(max_length=200, blank=True, null=True)
    description_uz = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    # base_price stored in integer smallest unit (tiyin)
    base_price = models.PositiveIntegerField(help_text="Price in UZS tiyin (1 UZS = 100 tiyin)")
    sku = models.CharField(max_length=100, blank=True)

    # Mahsulot rasmi — do'kon egasi maksimal 1 ta rasm yuklay oladi.
    image = models.ImageField(
        upload_to=product_image_upload_path,
        null=True,
        blank=True,
    )

    # Chegirma foizi (0 — chegirma yo'q)
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Chegirma foizi, 0 dan 100 gacha",
    )

    # Ombor / mahsulot soni
    track_stock = models.BooleanField(
        default=True,
        help_text="Agar yoqilgan bo'lsa, stock_qty 0 ga tushganda mahsulot avtomatik 'tugagan' bo'ladi",
    )
    stock_qty = models.PositiveIntegerField(
        default=0,
        help_text="Ombordagi mahsulot soni. Har xaridda kamayadi, 0 ga tushsa status avtomatik OUT_OF_STOCK bo'ladi",
    )

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

    @property
    def has_discount(self) -> bool:
        return self.discount_percent > 0

    @property
    def discounted_price(self) -> int:
        """Chegirma qo'llangandan keyingi narx (tiyin). Chegirma bo'lmasa base_price bilan teng."""
        if not self.discount_percent:
            return self.base_price
        discount = (self.base_price * self.discount_percent) // 100
        return max(self.base_price - discount, 0)

    def reduce_stock(self, qty: int = 1) -> None:
        """
        Xarid qilinganda ombordagi sonni kamaytiradi (race-condition'dan himoyalangan holda).
        Agar stock_qty 0 yoki undan kam bo'lib qolsa, mahsulot avtomatik 'tugagan'
        (OUT_OF_STOCK) statusiga o'tadi va is_available=False bo'ladi.
        `select_for_update()` bilan olingan instansiyada chaqirilishi tavsiya etiladi.
        """
        if not self.track_stock or qty <= 0:
            return

        new_qty = max(self.stock_qty - qty, 0)
        update_fields = ["stock_qty", "updated_at"]
        self.stock_qty = new_qty

        if new_qty <= 0 and self.status != ProductStatus.OUT_OF_STOCK:
            self.status = ProductStatus.OUT_OF_STOCK
            self.is_available = False
            update_fields += ["status", "is_available"]

        self.save(update_fields=update_fields)

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)

            # PNG kabi RGBA rasmlarni RGB ga o'tkazish
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Maksimal o'lcham
            img.thumbnail((1200, 1200))

            output = BytesIO()

            img.save(
                output,
                format="JPEG",
                quality=80,
                optimize=True,
            )

            output.seek(0)

            filename = os.path.splitext(self.image.name)[0] + ".jpg"

            self.image.save(
                filename,
                ContentFile(output.read()),
                save=False,
            )

        super().save(*args, **kwargs)


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
