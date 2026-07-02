from faker import Faker
from apps.accounts.models import (
    User,
    CustomerProfile,
    CourierProfile,
    DeviceToken,
)
from apps.accounts.constants import UserRole, VehicleType, Language
from apps.couriers.constants import CourierStatus

import random
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Fake ma'lumotlarni yaratish"

    def handle(self, *args, **options):
        print("Seed boshlanmoqda...")

        # Barcha seed kodlaringiz shu yerda bo'ladi

        print("Tugadi.")
fake = Faker("uz_UZ")

# self.stdout.write("Fake Userlar yaratilmoqda...")

for _ in range(100):

    role = random.choice([
        UserRole.CUSTOMER,
        UserRole.COURIER,
    ])

    user = User.objects.create(
        telegram_user_id=random.randint(100000000, 999999999),
        telegram_username=fake.user_name(),
        phone=f"+9989{random.randint(10000000,99999999)}",
        email=fake.email(),
        full_name=fake.name(),
        role=role,
        language=Language.UZ,
        is_verified=True,
        is_active=True,
    )

    DeviceToken.objects.create(
        user=user,
        token=fake.uuid4(),
        platform=random.choice(["android", "ios", "web"]),
        is_active=True,
    )

    if role == UserRole.CUSTOMER:
        CustomerProfile.objects.create(
            user=user,
            notes=fake.text(max_nb_chars=100),
        )

    elif role == UserRole.COURIER:
        CourierProfile.objects.create(
            user=user,
            vehicle_type=random.choice([
                VehicleType.MOTORBIKE,
                VehicleType.CAR,
                VehicleType.BICYCLE,
            ]),
            vehicle_number=f"01A{random.randint(100,999)}AA",
            passport_number=f"AA{random.randint(1000000,9999999)}",
            courier_status=random.choice([
                CourierStatus.ONLINE,
                CourierStatus.OFFLINE,
                CourierStatus.BUSY,
            ]),
            is_approved=random.choice([True, False]),
            current_lat=round(random.uniform(41.20, 41.40), 7),
            current_lng=round(random.uniform(69.15, 69.35), 7),
            rating=round(random.uniform(3.5, 5.0), 2),
            total_deliveries=random.randint(0, 1000),
            balance=random.randint(0, 10_000_000),
        )

# self.stdout.write(
#     self.style.SUCCESS("100 ta fake User yaratildi.")
# )

from faker import Faker
from apps.carts.models import Cart, CartItem, CartItemModifier
from apps.catalog.models import (
    Product,
    ProductVariant,
    ProductModifierOption,
)

import random

fake = Faker("uz_UZ")

# self.stdout.write("CartItem lar yaratilmoqda...")

carts = list(Cart.objects.all())
products = list(Product.objects.all())
variants = list(ProductVariant.objects.all())
modifier_options = list(ProductModifierOption.objects.all())

for _ in range(200):
    product = random.choice(products)

    variant = (
        random.choice(variants)
        if variants and random.choice([True, False])
        else None
    )

    qty = random.randint(1, 5)
    unit_price = product.price

    item = CartItem.objects.create(
        cart=random.choice(carts),
        product=product,
        variant=variant,
        qty=qty,
        unit_price=unit_price,
        snapshot_name=product.name_uz,
        instructions=fake.sentence(nb_words=5),
    )

    # Modifierlar
    if modifier_options:
        for modifier in random.sample(
            modifier_options,
            k=random.randint(0, min(3, len(modifier_options))),
        ):
            CartItemModifier.objects.create(
                cart_item=item,
                modifier_option=modifier,
                price=modifier.price,
                qty=random.randint(1, 2),
            )

# self.stdout.write(
#     self.style.SUCCESS("200 ta CartItem yaratildi.")
# )

from faker import Faker
from apps.carts.models import Cart, CartItem, CartItemModifier
from apps.catalog.models import (
    Product,
    ProductVariant,
    ProductModifierOption,
)

import random

fake = Faker("uz_UZ")

# self.stdout.write("CartItem lar yaratilmoqda...")

carts = list(Cart.objects.all())
products = list(Product.objects.all())
variants = list(ProductVariant.objects.all())
modifier_options = list(ProductModifierOption.objects.all())

for _ in range(200):
    product = random.choice(products)

    variant = (
        random.choice(variants)
        if variants and random.choice([True, False])
        else None
    )

    qty = random.randint(1, 5)
    unit_price = product.price

    item = CartItem.objects.create(
        cart=random.choice(carts),
        product=product,
        variant=variant,
        qty=qty,
        unit_price=unit_price,
        snapshot_name=product.name_uz,
        instructions=fake.sentence(nb_words=5),
    )

    # Modifierlar
    if modifier_options:
        for modifier in random.sample(
            modifier_options,
            k=random.randint(0, min(3, len(modifier_options))),
        ):
            CartItemModifier.objects.create(
                cart_item=item,
                modifier_option=modifier,
                price=modifier.price,
                qty=random.randint(1, 2),
            )

# self.stdout.write(
#     self.style.SUCCESS("200 ta CartItem yaratildi.")
# )

from apps.catalog.models import ProductCategory
from faker import Faker
import random

fake = Faker("uz_UZ")

# self.stdout.write("ProductCategory lar yaratilmoqda...")
from faker import Faker
from apps.catalog.models import Product
from apps.catalog.constants import ProductStatus
from apps.merchants.models import Merchant, MerchantBranch
from apps.catalog.models import ProductCategory

import random

fake = Faker("uz_UZ")

# self.stdout.write("Productlar yaratilmoqda...")

merchants = list(Merchant.objects.all())
branches = list(MerchantBranch.objects.all())
categories = list(ProductCategory.objects.all())

# if not merchants:
#     self.stdout.write(self.style.ERROR("Merchant topilmadi."))
#     return

# if not categories:
#     self.stdout.write(self.style.ERROR("Category topilmadi."))
#     return

for i in range(100):
    Product.objects.create(
        merchant=random.choice(merchants),
        branch=random.choice(branches) if branches else None,
        category=random.choice(categories),
        name_uz=f"Ovqat {i+1}",
        name_ru=f"Блюдо {i+1}",
        name_en=f"Food {i+1}",
        description_uz=fake.text(80),
        description_ru=fake.text(80),
        base_price=random.randint(30000, 250000),
        sku=f"SKU-{1000+i}",
        status=ProductStatus.ACTIVE,
        is_active=True,
        is_available=True,
        sort_order=i,
    )

# self.stdout.write(
#     self.style.SUCCESS("100 ta Product yaratildi.")
# )


from apps.catalog.models import ProductVariant, Product


for product in Product.objects.all():

    ProductVariant.objects.create(
        product=product,
        name_uz="Kichik",
        name_ru="Маленький",
        name_en="Small",
        price_delta=0,
        is_default=True,
    )

    ProductVariant.objects.create(
        product=product,
        name_uz="O'rta",
        name_ru="Средний",
        name_en="Medium",
        price_delta=10000,
    )

    ProductVariant.objects.create(
        product=product,
        name_uz="Katta",
        name_ru="Большой",
        name_en="Large",
        price_delta=20000,
    )

# self.stdout.write(
#     self.style.SUCCESS("Variantlar yaratildi.")
# )


from apps.catalog.models import ProductModifierGroup, Product
from apps.catalog.constants import ModifierGroupType


for product in Product.objects.all():

    ProductModifierGroup.objects.create(
        product=product,
        name_uz="Qo'shimchalar",
        name_ru="Добавки",
        group_type=ModifierGroupType.MULTIPLE,
        min_select=0,
        max_select=3,
        required=False,
    )

# self.stdout.write(
#     self.style.SUCCESS("ModifierGroup yaratildi.")
# )


from apps.catalog.models import (
    ProductModifierGroup,
    ProductModifierOption,
)

import random

options = [
    ("Pishloq", "Сыр"),
    ("Ketchup", "Кетчуп"),
    ("Mayonez", "Майонез"),
    ("Achchiq sous", "Острый соус"),
    ("Go'sht", "Мясо"),
]


for group in ProductModifierGroup.objects.all():

    for uz, ru in options:

        ProductModifierOption.objects.create(
            group=group,
            name_uz=uz,
            name_ru=ru,
            price_delta=random.randint(0, 20000),
            is_active=True,
        )

# self.stdout.write(
#     self.style.SUCCESS("ModifierOption yaratildi.")
# )
categories = []

# Asosiy kategoriyalar
for _ in range(10):
    category = ProductCategory.objects.create(
        name_uz=fake.word().capitalize(),
        name_ru=fake.word().capitalize(),
        name_en=fake.word().capitalize(),
        sort_order=random.randint(1, 100),
        is_active=random.choice([True, True, True, False]),
    )
    categories.append(category)

# Ichki kategoriyalar
for _ in range(20):
    ProductCategory.objects.create(
        parent=random.choice(categories),
        name_uz=fake.word().capitalize(),
        name_ru=fake.word().capitalize(),
        name_en=fake.word().capitalize(),
        sort_order=random.randint(1, 100),
        is_active=random.choice([True, True, True, False]),
    )

# self.stdout.write(
#     self.style.SUCCESS("30 ta ProductCategory yaratildi.")
# )
categories = [
    ("Burger", "Бургер"),
    ("Lavash", "Лаваш"),
    ("Pizza", "Пицца"),
    ("Ichimliklar", "Напитки"),
    ("Shashlik", "Шашлык"),
    ("Salatlar", "Салаты"),
    ("Shirinliklar", "Десерты"),
    ("Fast Food", "Фастфуд"),
    ("Milliy taomlar", "Национальные блюда"),
    ("Souslar", "Соусы"),
]

# self.stdout.write("ProductCategory lar yaratilmoqda...")

for i, (uz, ru) in enumerate(categories):
    ProductCategory.objects.get_or_create(
        name_uz=uz,
        defaults={
            "name_ru": ru,
            "name_en": uz,
            "sort_order": i + 1,
            "is_active": True,
        },
    )

# self.stdout.write(
#     self.style.SUCCESS(f"{len(categories)} ta ProductCategory yaratildi.")
# )