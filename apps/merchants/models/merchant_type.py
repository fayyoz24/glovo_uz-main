import uuid
from django.db import models


class MerchantType(models.Model):
    """
    Do'kon turi (restoran/fastfood, pharmacy, grocery, ...).
    `code` maydoni Merchant.type CharField qiymatlari bilan mos keladi
    (apps.merchants.constants.MerchantTypeCode), shu orqali ProductCategory
    ma'lum bir do'kon turiga FK bilan bog'lanadi.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(
        max_length=20,
        unique=True,
        help_text="Merchant.type qiymati bilan bir xil bo'lishi kerak, masalan: food, pharmacy",
    )
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    icon = models.ImageField(upload_to="merchants/type_icons/", null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "merchants_merchant_type"
        ordering = ["sort_order", "name_uz"]

    def __str__(self):
        return self.name_uz
