import random
from faker import Faker

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models.user import User
from apps.accounts.models.profiles import (
    CustomerProfile,
    CourierProfile,
)
from apps.accounts.models.otp import (
    OTPCode,
    TelegramBinding,
    OTPChannel,
)
from apps.accounts.models.device import DeviceToken

from apps.accounts.constants import (
    UserRole,
    Language,
    VehicleType,
)
from apps.couriers.constants import CourierStatus


fake = Faker()


class Command(BaseCommand):
    help = "Accounts modellarini fake ma'lumot bilan to'ldiradi"

    def handle(self, *args, **kwargs):

        users = []

        self.stdout.write("User yaratilyapti...")

        for i in range(50):

            role = random.choice([
                UserRole.CUSTOMER,
                UserRole.COURIER,
            ])

            user = User.objects.create_user(
                phone=f"+99890{random.randint(1000000,9999999)}",
                password="123456",
                full_name=fake.name(),
                email=fake.email(),
                role=role,
                language=random.choice([
                    Language.UZ,
                    Language.RU,
                    Language.EN,
                ]),
                is_active=True,
                is_verified=random.choice([True, False]),
            )

            users.append(user)

        self.stdout.write(self.style.SUCCESS("50 ta User yaratildi."))

        self.stdout.write("CustomerProfile yaratilyapti...")

        customers = User.objects.filter(role=UserRole.CUSTOMER)[:50]

        for user in customers:

            CustomerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "notes": fake.text(80),
                },
            )

        self.stdout.write(self.style.SUCCESS("CustomerProfile tayyor."))

        self.stdout.write("CourierProfile yaratilyapti...")

        couriers = User.objects.filter(role=UserRole.COURIER)[:50]

        for user in couriers:

            CourierProfile.objects.get_or_create(
                user=user,
                defaults={
                    "vehicle_type": random.choice([
                        VehicleType.BICYCLE,
                        VehicleType.MOTORBIKE,
                        VehicleType.CAR,
                    ]),
                    "vehicle_number": fake.license_plate(),
                    "passport_number": f"AA{random.randint(1000000,9999999)}",
                    "courier_status": random.choice(CourierStatus.values),
                    "is_approved": random.choice([True, False]),
                    "current_lat": 41.3111,
                    "current_lng": 69.2797,
                    "last_location_at": timezone.now(),
                    "rating": round(random.uniform(3.5, 5.0), 2),
                    "total_deliveries": random.randint(0, 500),
                    "balance": random.randint(0, 1000000),
                },
            )

        self.stdout.write(self.style.SUCCESS("CourierProfile tayyor."))

        self.stdout.write("OTPCode yaratilyapti...")

        for i in range(50):

            OTPCode.objects.create(
                phone=f"+99890{random.randint(1000000,9999999)}",
                code=str(random.randint(100000, 999999)),
                channel=random.choice(OTPChannel.values),
                is_used=random.choice([True, False]),
                attempts=random.randint(0, 5),
            )

        self.stdout.write(self.style.SUCCESS("OTPCode tayyor."))

        self.stdout.write("TelegramBinding yaratilyapti...")

        available_users = User.objects.exclude(
            telegram_binding__isnull=False
        )[:50]

        for user in available_users:

            TelegramBinding.objects.create(
                user=user,
                telegram_user_id=random.randint(
                    100000000,
                    999999999,
                ),
                telegram_username=fake.user_name(),
                is_confirmed=random.choice([True, False]),
            )

        self.stdout.write(self.style.SUCCESS("TelegramBinding tayyor."))

        self.stdout.write("DeviceToken yaratilyapti...")

        for i in range(50):

            DeviceToken.objects.create(
                user=random.choice(users),
                token=fake.uuid4(),
                platform=random.choice([
                    "ios",
                    "android",
                    "web",
                ]),
                is_active=random.choice([True, False]),
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Barcha modellar uchun fake ma'lumot yaratildi."
            )
        )