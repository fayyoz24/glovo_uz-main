import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import apps.catalog.validators


class Migration(migrations.Migration):

    dependencies = [
        ("merchants", "0002_merchanttype"),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Mahsulot rasmi (1 ta, default max hajm — 200 KB)",
                null=True,
                upload_to="catalog/product_images/",
                validators=[apps.catalog.validators.validate_product_image_size],
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="discount_percent",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Chegirma foizi, 0 dan 100 gacha",
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="track_stock",
            field=models.BooleanField(
                default=True,
                help_text="Agar yoqilgan bo'lsa, stock_qty 0 ga tushganda mahsulot avtomatik 'tugagan' bo'ladi",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="stock_qty",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Ombordagi mahsulot soni. Har xaridda kamayadi, 0 ga tushsa status avtomatik OUT_OF_STOCK bo'ladi",
            ),
        ),
        migrations.AddField(
            model_name="productcategory",
            name="merchant_type",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Kategoriya qaysi do'kon turiga tegishli (masalan: restoran/fastfood yoki pharmacy). "
                    "Bo'sh qoldirilsa, kategoriya barcha do'kon turlari uchun umumiy bo'ladi."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="categories",
                to="merchants.merchanttype",
            ),
        ),
        migrations.AddIndex(
            model_name="productcategory",
            index=models.Index(fields=["merchant_type", "is_active"], name="catalog_pro_merchan_9a6333_idx"),
        ),
    ]
