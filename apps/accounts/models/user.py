import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.accounts.constants import UserRole, Language
from apps.accounts.utils.phone import normalize_phone


class UserManager(BaseUserManager):
    def create_user(self, telegram_user_id, password=None, **extra_fields):
        if not telegram_user_id:
            raise ValueError("Telegram user ID talab qilinadi")
        user = self.model(telegram_user_id=telegram_user_id, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_user_id, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(telegram_user_id, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Yagona auth identifikatori — Telegram bot orqali tasdiqlangan akkaunt.
    telegram_user_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_username = models.CharField(max_length=100, blank=True)

    # Telefon endi auth uchun ishlatilmaydi (faqat kuryer/buyurtma uchun ixtiyoriy ma'lumot).
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.CHOICES,
        default=UserRole.CUSTOMER,
    )
    language = models.CharField(
        max_length=5,
        choices=Language.CHOICES,
        default=Language.UZ,   # FIX: Uzbekiston bozori uchun UZ default
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "telegram_user_id"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["telegram_user_id"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.telegram_username or self.telegram_user_id} ({self.role})"

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

    @property
    def is_courier(self):
        return self.role == UserRole.COURIER

    @property
    def is_merchant_staff(self):
        return self.role in (UserRole.MERCHANT_OWNER, UserRole.MERCHANT_MANAGER)

    @property
    def is_admin_user(self):
        return self.role in (UserRole.ADMIN, UserRole.SUPPORT)

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)
