from django.utils import timezone
from apps.accounts.models import User, TelegramLoginCode


def get_user_by_id(user_id) -> User | None:
    return User.objects.filter(id=user_id, is_active=True).first()


def get_user_by_telegram_id(telegram_user_id: int) -> User | None:
    return User.objects.filter(telegram_user_id=telegram_user_id).first()


def get_login_code_by_code(code: str) -> TelegramLoginCode | None:
    """Frontend kiritgan kodni topadi (holatidan qat'i nazar — service qatlami tekshiradi)."""
    return TelegramLoginCode.objects.filter(code=code).order_by("-created_at").first()


def get_latest_code_for_telegram_user(telegram_user_id: int) -> TelegramLoginCode | None:
    """Bot tomonidan cooldown tekshiruvi uchun ishlatiladi."""
    return (
        TelegramLoginCode.objects.filter(telegram_user_id=telegram_user_id)
        .order_by("-created_at")
        .first()
    )
