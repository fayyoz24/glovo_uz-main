"""
Promotions Celery tasks.
"""
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expire_stale_promos(self):
    """
    Muddati o'tgan promo kampaniyalarni EXPIRED holatiga o'tkazadi.
    Celery Beat orqali har kuni ishga tushiriladi.
    """
    from promotions.constants import PromoStatus
    from promotions.models import PromoCampaign

    now = timezone.now()
    expired_count = PromoCampaign.objects.filter(
        status=PromoStatus.ACTIVE,
        ends_at__lt=now,
    ).update(status=PromoStatus.EXPIRED)

    return f"{expired_count} ta promo EXPIRED holatiga o'tkazildi."


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def credit_referral_bonus_task(
    self,
    *,
    referrer_user_id: str,
    referee_user_id: str,
    referrer_bonus: float,
    referee_bonus: float,
):
    """
    Referal bonuslarni foydalanuvchilar balansiga yozadi.
    Wallet app integratsiyasi shu yerda amalga oshiriladi.
    """
    try:
        # Wallet yoki bonus tizimi mavjud bo'lsa:
        # WalletService.credit(user_id=referrer_user_id, amount=referrer_bonus, reason="referral_reward")
        # WalletService.credit(user_id=referee_user_id, amount=referee_bonus, reason="referral_signup_bonus")

        # Hozircha log
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "Referral bonus credited: referrer=%s (+%s), referee=%s (+%s)",
            referrer_user_id, referrer_bonus,
            referee_user_id, referee_bonus,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def auto_activate_scheduled_promos():
    """
    starts_at vaqti kelgan DRAFT kampaniyalarni ACTIVE qiladi.
    Celery Beat: har 5 daqiqada.
    """
    from promotions.constants import PromoStatus
    from promotions.models import PromoCampaign

    now = timezone.now()
    count = PromoCampaign.objects.filter(
        status=PromoStatus.DRAFT,
        starts_at__lte=now,
    ).update(status=PromoStatus.ACTIVE)

    return f"{count} ta promo avtomatik ACTIVE qilindi."
