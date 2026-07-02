from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name="apps.carts.tasks.expire_old_carts", bind=True, max_retries=3)
def expire_old_carts(self):
    """
    Muddati o'tgan (expires_at < now) active cartlarni EXPIRED ga o'tkazadi.
    Har 6 soatda ishga tushadi.
    """
    try:
        from apps.carts.models import Cart
        from apps.carts.constants import CartStatus

        updated = Cart.objects.filter(
            status=CartStatus.ACTIVE,
            expires_at__lt=timezone.now(),
        ).update(status=CartStatus.EXPIRED)

        logger.info(f"[Cart Expire] {updated} ta cart EXPIRED ga o'tkazildi.")
        return {"expired": updated}
    except Exception as exc:
        logger.error(f"[Cart Expire] Xatolik: {exc}")
        raise self.retry(exc=exc, countdown=60 * 10)


@shared_task(name="apps.carts.tasks.notify_abandoned_carts", bind=True, max_retries=3)
def notify_abandoned_carts(self):
    """
    6-24 soat ichida to'ldirilmagan (abandoned) cartlar egalariga
    push notification yuboradi va cart statusini ABANDONED ga o'tkazadi.
    Har kuni 10:00 da ishga tushadi.
    """
    try:
        from apps.carts.models import Cart
        from apps.carts.constants import CartStatus

        threshold_start = timezone.now() - timezone.timedelta(hours=24)
        threshold_end = timezone.now() - timezone.timedelta(hours=6)

        abandoned_carts = Cart.objects.filter(
            status=CartStatus.ACTIVE,
            updated_at__gte=threshold_start,
            updated_at__lte=threshold_end,
        ).select_related("user").prefetch_related("items")

        notified = 0
        for cart in abandoned_carts:
            if not cart.items.exists():
                continue

            # TODO: push notification yuborish
            # send_push_notification.delay(
            #     user_id=str(cart.user.id),
            #     title="Savatingizda mahsulotlar qoldi!",
            #     body="Buyurtmangizni yakunlang va tezroq yetkazib beramiz.",
            # )

            cart.status = CartStatus.ABANDONED
            cart.save(update_fields=["status", "updated_at"])
            notified += 1

        logger.info(f"[Abandoned Carts] {notified} ta foydalanuvchiga bildirishnoma yuborildi.")
        return {"notified": notified}
    except Exception as exc:
        logger.error(f"[Abandoned Carts] Xatolik: {exc}")
        raise self.retry(exc=exc, countdown=60 * 15)
