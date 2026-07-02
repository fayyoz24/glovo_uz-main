from apps.catalog.models import ProductCategory
from django.core.management.base import BaseCommand

print("ProductCategory lar yaratilmoqda...")
class Command(BaseCommand):
    help = "Fake ma'lumotlarni yaratish"

    def handle(self, *args, **options):
        print("Seed boshlanmoqda...")

        # Barcha seed kodlaringiz shu yerda bo'ladi

        print("Tugadi.")


from faker import Faker
from apps.accounts.models import User
from apps.merchants.models import Merchant
from apps.merchants.constants import MerchantType, MerchantStatus

from django.utils.text import slugify
import random

fake = Faker("uz_UZ")

print("Merchantlar yaratilmoqda...")

users = list(User.objects.all())

for i in range(20):
    name = fake.company()

    Merchant.objects.create(
        name=name,
        slug=f"{slugify(name)}-{i}",
        type=random.choice([
            MerchantType.FOOD,
        ]),
        description=fake.text(100),
        rating_avg=round(random.uniform(3.5, 5.0), 2),
        total_reviews=random.randint(10, 500),
        status=MerchantStatus.ACTIVE,
        owner=random.choice(users) if users else None,
    )

print("20 ta Merchant yaratildi.")

from faker import Faker
from apps.merchants.models import MerchantBranch, Merchant

import random

fake = Faker("uz_UZ")
from faker import Faker
from apps.catalog.models import Product, ProductCategory
from apps.catalog.constants import ProductStatus
from apps.merchants.models import Merchant, MerchantBranch

import random

fake = Faker("uz_UZ")

print("Productlar yaratilmoqda...")

merchants = list(Merchant.objects.all())
branches = list(MerchantBranch.objects.all())
categories = list(ProductCategory.objects.all())

if not merchants:
    print("Merchant topilmadi!")
    exit()

if not categories:
    print("ProductCategory topilmadi!")
    exit()

foods = [
    ("Lavash", "Лаваш"),
    ("Burger", "Бургер"),
    ("Pizza", "Пицца"),
    ("Donar", "Донар"),
    ("Hot Dog", "Хот-дог"),
    ("Shashlik", "Шашлык"),
    ("Somsa", "Самса"),
    ("Manti", "Манты"),
    ("Osh", "Плов"),
    ("Cola", "Кола"),
    ("Fanta", "Фанта"),
    ("Pepsi", "Пепси"),
]

for i in range(100):
    merchant = random.choice(merchants)

    merchant_branches = list(
        MerchantBranch.objects.filter(merchant=merchant)
    )

    Product.objects.create(
        merchant=merchant,
        branch=random.choice(merchant_branches) if merchant_branches else None,
        category=random.choice(categories),
        name_uz=random.choice(foods)[0],
        name_ru=random.choice(foods)[1],
        name_en=fake.word().title(),
        description_uz=fake.text(100),
        description_ru=fake.text(100),
        base_price=random.randint(25000, 180000),
        sku=f"SKU-{1000+i}",
        status=ProductStatus.ACTIVE,
        is_active=True,
        is_available=True,
        sort_order=i,
    )

print("100 ta Product yaratildi.")


from apps.catalog.models import Product, ProductVariant

print("ProductVariant lar yaratilmoqda...")

variants = [
    ("Kichik", "Маленький", "Small", 0, True),
    ("O'rta", "Средний", "Medium", 10000, False),
    ("Katta", "Большой", "Large", 20000, False),
]

for product in Product.objects.all():

    for index, (uz, ru, en, delta, default) in enumerate(variants, start=1):

        ProductVariant.objects.create(
            product=product,
            name_uz=uz,
            name_ru=ru,
            name_en=en,
            price_delta=delta,
            is_default=default,
            is_active=True,
            sort_order=index,
        )

print("ProductVariant lar yaratildi.")

from apps.catalog.models import Product, ProductModifierGroup
from apps.catalog.constants import ModifierGroupType

print("ProductModifierGroup lar yaratilmoqda...")

for product in Product.objects.all():

    ProductModifierGroup.objects.create(
        product=product,
        name_uz="Qo'shimchalar",
        name_ru="Добавки",
        group_type=ModifierGroupType.MULTIPLE,
        min_select=0,
        max_select=3,
        required=False,
        sort_order=1,
        is_active=True,
    )

    ProductModifierGroup.objects.create(
        product=product,
        name_uz="Sous tanlang",
        name_ru="Выберите соус",
        group_type=ModifierGroupType.SINGLE,
        min_select=1,
        max_select=1,
        required=True,
        sort_order=2,
        is_active=True,
    )

print("ProductModifierGroup lar yaratildi.")

from apps.catalog.models import (
    ProductModifierGroup,
    ProductModifierOption,
)

import random

print("ProductModifierOption lar yaratilmoqda...")

options = [
    ("Ketchup", "Кетчуп"),
    ("Mayonez", "Майонез"),
    ("Achchiq sous", "Острый соус"),
    ("Pishloq", "Сыр"),
    ("Go'sht", "Мясо"),
    ("Pomidor", "Помидор"),
    ("Bodring", "Огурец"),
]

for group in ProductModifierGroup.objects.all():

    random.shuffle(options)

    for index, (uz, ru) in enumerate(options[:4], start=1):

        ProductModifierOption.objects.create(
            group=group,
            name_uz=uz,
            name_ru=ru,
            price_delta=random.randint(0, 20000),
            is_active=True,
            sort_order=index,
        )

print("ProductModifierOption lar yaratildi.")
print("MerchantBranch yaratilmoqda...")
from faker import Faker
from django.utils.text import slugify
from apps.accounts.models import User
from apps.merchants.models import Merchant
from apps.merchants.constants import MerchantType, MerchantStatus

import random

fake = Faker("uz_UZ")

print("Merchantlar yaratilmoqda...")

users = list(User.objects.all())

merchant_data = {
    MerchantType.FOOD: [
        "Evos",
        "Oqtepa Lavash",
        "Les Ailes",
        "Max Way",
        "Feed Up",
        "KFC",
        "Bellissimo Pizza",
        "Chopar Pizza",
    ],
    MerchantType.GROCERY: [
        "Korzinka",
        "Havas",
        "Makro",
        "Baraka Market",
        "Bi1",
    ],
    MerchantType.PHARMACY: [
        "Dori-Darmon",
        "999 Dorixona",
        "Apteka Plus",
        "OXY Med",
    ],
    MerchantType.FLOWERS: [
        "Flowers House",
        "Lola Flowers",
        "Florist Uz",
        "Rose Garden",
    ],
    MerchantType.EXPRESS: [
        "Express24",
        "Quick Delivery",
        "Speed Express",
        "Fast Courier",
    ],
}

merchant_types = [choice[0] for choice in MerchantType.CHOICES]

for i in range(30):

    merchant_type = random.choice(merchant_types)
    name = random.choice(merchant_data[merchant_type])

    Merchant.objects.create(
        name=f"{name} {i+1}",
        slug=f"{slugify(name)}-{i+1}",
        type=merchant_type,
        description=fake.text(100),
        rating_avg=round(random.uniform(3.5, 5.0), 2),
        total_reviews=random.randint(10, 1000),
        status=MerchantStatus.ACTIVE,
        owner=random.choice(users) if users else None,
    )

print("30 ta Merchant yaratildi.")
merchants = list(Merchant.objects.all())

for merchant in merchants:

    for i in range(random.randint(1, 3)):

        MerchantBranch.objects.create(
            merchant=merchant,
            name=f"{merchant.name} Filial {i+1}",
            phone=f"+9989{random.randint(10000000,99999999)}",
            address_text=fake.address(),
            latitude=41.31 + random.uniform(-0.05, 0.05),
            longitude=69.24 + random.uniform(-0.05, 0.05),
            service_radius_km=random.randint(3, 10),
            prep_time_min=random.randint(10, 40),
            is_open=random.choice([True, False]),
            accepting_orders=True,
        )

print("MerchantBranch yaratildi.")
categories = [
    ("Burger", "Бургеры", "Burger"),
    ("Lavash", "Лаваш", "Lavash"),
    ("Pizza", "Пицца", "Pizza"),
    ("Donar", "Донар", "Doner"),
    ("Shashlik", "Шашлык", "Kebab"),
    ("Somsa", "Самса", "Samsa"),
    ("Ichimliklar", "Напитки", "Drinks"),
    ("Shirinliklar", "Десерты", "Desserts"),
    ("Salatlar", "Салаты", "Salads"),
    ("Souslar", "Соусы", "Sauces"),
]

parent_categories = []

# Asosiy kategoriyalar
for index, (uz, ru, en) in enumerate(categories, start=1):
    category = ProductCategory.objects.create(
        name_uz=uz,
        name_ru=ru,
        name_en=en,
        sort_order=index,
        is_active=True,
    )
    parent_categories.append(category)

# Har bir kategoriyaga 2 ta subkategoriya
for parent in parent_categories:
    for i in range(2):
        ProductCategory.objects.create(
            parent=parent,
            name_uz=f"{parent.name_uz} {i+1}",
            name_ru=f"{parent.name_ru} {i+1}",
            name_en=f"{parent.name_en} {i+1}",
            sort_order=i + 1,
            is_active=True,
        )

print("30 ta ProductCategory yaratildi.")