import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.accounts.tasks.clean_expired_login_codes")
def clean_expired_login_codes(days: int = 1) -> dict:
    """
    Periodic task: eskirgan/ishlatilgan Telegram login kodlarini tozalaydi.
    Schedule: har kecha, Celery Beat orqali.
    """
    from apps.accounts.models import TelegramLoginCode

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = TelegramLoginCode.objects.filter(created_at__lt=cutoff).delete()

    logger.info("clean_expired_login_codes: deleted=%d", deleted)
    return {"deleted": deleted}
