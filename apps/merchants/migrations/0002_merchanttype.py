import uuid
from django.db import migrations, models


SEED_TYPES = [
    ("food", "Restoran / Fastfood", "Ресторан / Фастфуд", "Restaurant / Fastfood", 1),
    ("grocery", "Grocery / Market", "Продуктовый магазин", "Grocery", 2),
    ("pharmacy", "Dorixona", "Аптека", "Pharmacy", 3),
    ("flowers", "Gullar", "Цветы", "Flowers", 4),
    ("express", "Express yetkazish", "Экспресс доставка", "Express Delivery", 5),
]


def seed_merchant_types(apps, schema_editor):
    MerchantType = apps.get_model("merchants", "MerchantType")
    for code, name_uz, name_ru, name_en, sort_order in SEED_TYPES:
        MerchantType.objects.get_or_create(
            code=code,
            defaults={
                "id": uuid.uuid4(),
                "name_uz": name_uz,
                "name_ru": name_ru,
                "name_en": name_en,
                "sort_order": sort_order,
                "is_active": True,
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("merchants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MerchantType",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "code",
                    models.SlugField(
                        max_length=20,
                        unique=True,
                        help_text="Merchant.type qiymati bilan bir xil bo'lishi kerak, masalan: food, pharmacy",
                    ),
                ),
                ("name_uz", models.CharField(max_length=100)),
                ("name_ru", models.CharField(max_length=100)),
                ("name_en", models.CharField(blank=True, max_length=100)),
                ("icon", models.ImageField(blank=True, null=True, upload_to="merchants/type_icons/")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "merchants_merchant_type",
                "ordering": ["sort_order", "name_uz"],
            },
        ),
        migrations.RunPython(seed_merchant_types, noop_reverse),
    ]
