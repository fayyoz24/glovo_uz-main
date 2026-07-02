from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, TelegramLoginCode
from apps.accounts.constants import (
    UserRole,
    LOGIN_CODE_COOLDOWN_SECONDS,
    LOGIN_CODE_MAX_ATTEMPTS,
)
from apps.accounts.exceptions import (
    LoginCodeExpired,
    LoginCodeInvalid,
    LoginCodeMaxAttemptsReached,
    LoginCodeCooldownActive,
    UserInactive,
)
from apps.accounts.selectors.user import (
    get_login_code_by_code,
    get_latest_code_for_telegram_user,
)


def generate_login_code(
    telegram_user_id: int,
    telegram_username: str = "",
    telegram_first_name: str = "",
) -> TelegramLoginCode:
    """
    Bot /start (yoki "yangi kod") buyrug'ida chaqiriladi.
    Shu telegram foydalanuvchisi uchun bir martalik login kodi yaratadi.

    Raises:
        LoginCodeCooldownActive – juda tez-tez so'ralsa
    """
    last_code = get_latest_code_for_telegram_user(telegram_user_id)
    if last_code:
        elapsed = (timezone.now() - last_code.created_at).total_seconds()
        if elapsed < LOGIN_CODE_COOLDOWN_SECONDS:
            raise LoginCodeCooldownActive()

    return TelegramLoginCode.generate_for(
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
        telegram_first_name=telegram_first_name,
    )


def verify_login_code(code: str) -> dict:
    """
    Frontend "Kodni kiriting" oynasidan kod yuborilganda chaqiriladi.
    Kodni tekshiradi, User'ni topadi yoki (birinchi marta bo'lsa) yaratadi,
    JWT tokenlarni qaytaradi.

    Raises:
        LoginCodeInvalid          – bunday kod umuman topilmadi yoki allaqachon ishlatilgan
        LoginCodeMaxAttemptsReached
        LoginCodeExpired
        UserInactive
    """
    login_code = get_login_code_by_code(code)

    if login_code is None or login_code.is_used:
        raise LoginCodeInvalid()

    if login_code.attempts >= LOGIN_CODE_MAX_ATTEMPTS:
        raise LoginCodeMaxAttemptsReached()

    login_code.increment_attempts()

    if login_code.is_expired:
        raise LoginCodeExpired()

    with transaction.atomic():
        login_code.mark_used()

        user, created = User.objects.get_or_create(
            telegram_user_id=login_code.telegram_user_id,
            defaults={
                "role": UserRole.CUSTOMER,
                "is_verified": True,
                "telegram_username": login_code.telegram_username,
                "full_name": login_code.telegram_first_name,
            },
        )

        if not created and not user.is_active:
            raise UserInactive()

        update_fields = []
        if login_code.telegram_username and user.telegram_username != login_code.telegram_username:
            user.telegram_username = login_code.telegram_username
            update_fields.append("telegram_username")
        if not user.is_verified:
            user.is_verified = True
            update_fields.append("is_verified")
        if update_fields:
            user.save(update_fields=update_fields)

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user_id": str(user.id),
        "role": user.role,
        "is_new": created,
    }
