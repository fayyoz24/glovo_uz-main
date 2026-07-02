class UserRole:
    CUSTOMER = "customer"
    COURIER = "courier"
    MERCHANT_OWNER = "merchant_owner"
    MERCHANT_MANAGER = "merchant_manager"
    ADMIN = "admin"
    SUPPORT = "support"

    CHOICES = [
        (CUSTOMER, "Customer"),
        (COURIER, "Courier"),
        (MERCHANT_OWNER, "Merchant Owner"),
        (MERCHANT_MANAGER, "Merchant Manager"),
        (ADMIN, "Admin"),
        (SUPPORT, "Support"),
    ]


class VehicleType:
    BICYCLE = "bicycle"
    MOTORBIKE = "motorbike"
    CAR = "car"
    FOOT = "foot"

    CHOICES = [
        (BICYCLE, "Bicycle"),
        (MOTORBIKE, "Motorbike"),
        (CAR, "Car"),
        (FOOT, "On Foot"),
    ]


class Language:
    UZ = "uz"
    RU = "ru"
    EN = "en"

    CHOICES = [
        (UZ, "Uzbek"),
        (RU, "Russian"),
        (EN, "English"),
    ]


# ─── Telegram login code (42.uz uslubida) ──────────────────────────────────
# Foydalanuvchi @bot ga kiradi, botdan bir martalik kod oladi va shu kodni
# saytga kiritadi. Boshqa hech qanday auth usuli (SMS/parol) mavjud emas.
LOGIN_CODE_LENGTH = 6
LOGIN_CODE_EXPIRY_SECONDS = 60        # kod 1 daqiqa amal qiladi
LOGIN_CODE_COOLDOWN_SECONDS = 5       # botda ketma-ket "yangi kod" so'rovlari orasidagi minimal interval
LOGIN_CODE_MAX_ATTEMPTS = 5
