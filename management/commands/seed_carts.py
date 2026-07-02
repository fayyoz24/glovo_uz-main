from apps.analytics.models import DailyAnalyticsSnapshot
from datetime import timedelta
from django.utils import timezone
import random

self.stdout.write("DailyAnalyticsSnapshot yaratilmoqda...")

for i in range(50):
    DailyAnalyticsSnapshot.objects.get_or_create(
        date=timezone.now().date() - timedelta(days=i),
        defaults={
            "total_users": random.randint(100, 10000),
            "total_customers": random.randint(50, 8000),
            "total_merchants": random.randint(10, 500),
            "total_couriers": random.randint(20, 1000),
            "active_couriers": random.randint(10, 500),

            "total_orders": random.randint(100, 10000),
            "delivered_orders": random.randint(50, 9000),
            "cancelled_orders": random.randint(0, 500),

            "gross_revenue": random.randint(1_000_000, 50_000_000),
            "paid_orders_amount": random.randint(500_000, 40_000_000),
            "refunded_amount": random.randint(0, 3_000_000),

            "avg_order_value": random.randint(30_000, 250_000),
            "avg_delivery_minutes": round(random.uniform(10, 60), 2),
        },
    )

self.stdout.write(
    self.style.SUCCESS("50 ta DailyAnalyticsSnapshot yaratildi.")
)

from apps.catalog.models import ProductCategory

categories = []

self.stdout.write("Category yaratilmoqda...")

for i in range(50):
    category = ProductCategory.objects.create(
        name_uz=f"Ovqat turi {i+1}",
        name_ru=f"Категория {i+1}",
        name_en=f"Category {i+1}",
        sort_order=i,
        is_active=True,
    )
    categories.append(category)

self.stdout.write(self.style.SUCCESS("50 ta Category yaratildi."))

from apps.catalog.models import Product
from apps.merchants.models import Merchant, MerchantBranch
from apps.catalog.constants import ProductStatus

merchants = list(Merchant.objects.all())
branches = list(MerchantBranch.objects.all())

products = []

self.stdout.write("Product yaratilmoqda...")

for i in range(50):
    product = Product.objects.create(
        merchant=random.choice(merchants),
        branch=random.choice(branches) if branches else None,
        category=random.choice(categories),
        name_uz=fake.word().capitalize(),
        name_ru=fake.word().capitalize(),
        name_en=fake.word().capitalize(),
        description_uz=fake.sentence(),
        description_ru=fake.sentence(),
        base_price=random.randint(30000, 250000),
        sku=f"SKU-{1000+i}",
        status=random.choice(ProductStatus.values),
        is_active=True,
        is_available=random.choice([True, False]),
        sort_order=i,
    )

    products.append(product)

self.stdout.write(self.style.SUCCESS("50 ta Product yaratildi."))

from apps.catalog.models import ProductVariant

variant_names = [
    ("Kichik", "Маленький"),
    ("O'rta", "Средний"),
    ("Katta", "Большой"),
]

self.stdout.write("Variant yaratilmoqda...")

for i in range(50):

    uz, ru = random.choice(variant_names)

    ProductVariant.objects.create(
        product=random.choice(products),
        name_uz=uz,
        name_ru=ru,
        name_en=uz,
        price_delta=random.randint(-10000, 50000),
        is_default=(i % 3 == 0),
        is_active=True,
        sort_order=i,
    )

self.stdout.write(self.style.SUCCESS("50 ta Variant yaratildi."))

from apps.catalog.models import ProductModifierGroup
from apps.catalog.constants import ModifierGroupType

groups = []

group_names = [
    ("Sous", "Соус"),
    ("Ichimlik", "Напиток"),
    ("Qo'shimcha", "Добавка"),
    ("Hajm", "Размер"),
]

self.stdout.write("ModifierGroup yaratilmoqda...")

for i in range(50):

    uz, ru = random.choice(group_names)

    group = ProductModifierGroup.objects.create(
        product=random.choice(products),
        name_uz=uz,
        name_ru=ru,
        group_type=random.choice(ModifierGroupType.values),
        min_select=0,
        max_select=random.randint(1, 3),
        required=random.choice([True, False]),
        sort_order=i,
        is_active=True,
    )

    groups.append(group)

self.stdout.write(self.style.SUCCESS("50 ta ModifierGroup yaratildi."))

from apps.catalog.models import ProductModifierOption

option_names = [
    ("Ketchup", "Кетчуп"),
    ("Mayonez", "Майонез"),
    ("Pishloq", "Сыр"),
    ("Achchiq sous", "Острый соус"),
    ("Cola", "Кола"),
]

self.stdout.write("ModifierOption yaratilmoqda...")

for i in range(50):

    uz, ru = random.choice(option_names)

    ProductModifierOption.objects.create(
        group=random.choice(groups),
        name_uz=uz,
        name_ru=ru,
        price_delta=random.randint(0, 30000),
        is_active=True,
        sort_order=i,
    )

self.stdout.write(self.style.SUCCESS("50 ta ModifierOption yaratildi."))

from apps.couriers.models import CourierLocationPing

self.stdout.write("CourierLocationPing yaratilmoqda...")

for _ in range(50):
    CourierLocationPing.objects.create(
        courier=random.choice(couriers),
        latitude=round(random.uniform(41.20, 41.40), 7),
        longitude=round(random.uniform(69.15, 69.35), 7),
        accuracy=round(random.uniform(3, 20), 2),
    )

self.stdout.write(
    self.style.SUCCESS("50 ta CourierLocationPing yaratildi.")
)

from apps.couriers.models import CourierShift
from apps.couriers.constants import ShiftStatus

self.stdout.write("CourierShift yaratilmoqda...")

for _ in range(50):

    start = fake.date_time_between(start_date="-30d", end_date="now")

    CourierShift.objects.create(
        courier=random.choice(couriers),
        start_time=start,
        end_time=start + timedelta(hours=random.randint(4, 10)),
        status=random.choice(ShiftStatus.values),
        deliveries_count=random.randint(0, 30),
        total_earned=random.randint(50000, 700000),
    )

self.stdout.write(
    self.style.SUCCESS("50 ta CourierShift yaratildi.")
)

from apps.couriers.models import CourierEarning

self.stdout.write("CourierEarning yaratilmoqda...")

for _ in range(50):

    base_fee = random.randint(10000, 40000)
    bonus = random.randint(0, 10000)
    tip = random.randint(0, 15000)

    CourierEarning.objects.create(
        courier=random.choice(couriers),
        order=None,
        amount=base_fee + bonus + tip,
        base_fee=base_fee,
        bonus=bonus,
        tip=tip,
        note=fake.sentence(),
    )

self.stdout.write(
    self.style.SUCCESS("50 ta CourierEarning yaratildi.")
)

