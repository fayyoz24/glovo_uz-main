"""
Celery tasks — orders app uchun asinxron vazifalar.
"""
try:
    from celery import shared_task
except ImportError:
    # Celery o'rnatilmagan bo'lsa, stub
    def shared_task(func):
        return func


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def notify_merchant_new_order(self, order_id: str):
    """Yangi buyurtma haqida merchantga push/SMS xabarnomasi yuboradi."""
    try:
        from apps.orders.models import Order
        order = Order.objects.select_related("branch__merchant").get(id=order_id)
        # TODO: notifications app bilan integratsiya
        print(f"[TASK] Merchant notified: Order #{order.public_id}")
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def notify_order_status_changed(self, order_id: str, new_status: str):
    """Buyurtma holati o'zgarganda mijozga bildirishnoma yuboradi."""
    try:
        from apps.orders.models import Order
        order = Order.objects.select_related("customer").get(id=order_id)
        # TODO: push notification / websocket event
        print(f"[TASK] Customer notified: Order #{order.public_id} → {new_status}")
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def auto_cancel_unpaid_orders():
    """
    To'lanmagan buyurtmalarni avtomatik bekor qiladi (Celery Beat orqali ishlaydi).
    Har 5 daqiqada tekshiradi.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.orders.models import Order
    from apps.orders.constants import OrderStatus, PaymentStatus, CancelReason
    from apps.orders.services import cancel_order

    deadline = timezone.now() - timedelta(minutes=15)
    unpaid_orders = Order.objects.filter(
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        placed_at__lt=deadline,
    ).exclude(payment_method="cash")  # COD bekor qilinmaydi

    cancelled_count = 0
    for order in unpaid_orders:
        try:
            cancel_order(
                order=order,
                reason=CancelReason.PAYMENT_FAILED,
                note="15 daqiqa ichida to'lov amalga oshmadi.",
            )
            cancelled_count += 1
        except Exception:
            pass

    print(f"[TASK] Auto-cancelled {cancelled_count} unpaid orders")
    return cancelled_count


@shared_task
def cleanup_stale_carts():
    """Muddati o'tgan savatlarni tozalaydi."""
    from django.utils import timezone
    from apps.carts.models import Cart
    from apps.carts.constants import CartStatus

    result = Cart.objects.filter(
        status=CartStatus.ACTIVE,
        expires_at__lt=timezone.now(),
    ).update(status=CartStatus.EXPIRED)

    print(f"[TASK] Expired {result} stale carts")
    return result
