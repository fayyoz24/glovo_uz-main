import random
import string
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.accounts.constants import LOGIN_CODE_EXPIRY_SECONDS, LOGIN_CODE_LENGTH


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=LOGIN_CODE_LENGTH))


def login_code_expiry_time():
    return timezone.now() + timedelta(seconds=LOGIN_CODE_EXPIRY_SECONDS)


class TelegramLoginCode(models.Model):
    """
    42.uz uslubidagi bir martalik login kodi.

    Oqim:
      1. Foydalanuvchi Telegram botga /start yuboradi.
      2. Bot Django'dan yangi kod so'raydi (generate_for) va uni foydalanuvchiga yuboradi.
      3. Foydalanuvchi shu kodni saytdagi "Kodni kiriting" oynasiga kiritadi.
      4. Backend kodni tekshiradi va shu telegram_user_id uchun User'ni topadi
         yoki (birinchi marta bo'lsa) avtomatik yaratadi.

    Kod hech qanday mavjud User bilan oldindan bog'liq emas — Telegram akkaunt
    o'zi identifikator vazifasini bajaradi.
    """
    MAX_ATTEMPTS = 5

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=8, db_index=True)
    telegram_user_id = models.BigIntegerField(db_index=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    telegram_first_name = models.CharField(max_length=150, blank=True)
    is_used = models.BooleanField(default=False, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=login_code_expiry_time, db_index=True)

    class Meta:
        db_table = "accounts_telegram_login_code"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["code", "is_used"]),
            models.Index(fields=["telegram_user_id", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"LoginCode({self.code}, tg:{self.telegram_user_id})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_blocked(self) -> bool:
        return self.attempts >= self.MAX_ATTEMPTS

    @property
    def can_verify(self) -> bool:
        return not self.is_used and not self.is_expired and not self.is_blocked

    def increment_attempts(self) -> None:
        self.attempts += 1
        self.save(update_fields=["attempts"])

    def mark_used(self) -> None:
        self.is_used = True
        self.save(update_fields=["is_used"])

    @classmethod
    def generate_for(
        cls,
        telegram_user_id: int,
        telegram_username: str = "",
        telegram_first_name: str = "",
    ) -> "TelegramLoginCode":
        """Shu telegram foydalanuvchisi uchun avvalgi faol kodlarni bekor qilib, yangisini yaratadi."""
        cls.objects.filter(telegram_user_id=telegram_user_id, is_used=False).update(is_used=True)
        return cls.objects.create(
            code=_generate_code(),
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
        )
