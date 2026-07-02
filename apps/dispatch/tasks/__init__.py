"""
Dispatch Celery tasklari:
- offer timeout tekshiruvi
- reassignment loop
- admin escalation
"""
try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func


@shared_task(bind=True, max_retries=1)
def handle_offer_timeout(self, assignment_id: str):
    """
    Kuryer OFFER_TIMEOUT_SECONDS ichida javob bermasa chaqiriladi.
    """
    try:
        from apps.dispatch.models import CourierAssignment
        from apps.dispatch.constants import AssignmentStatus
        from apps.dispatch.services import reassign_or_escalate

        try:
            assignment = CourierAssignment.objects.select_related("order").get(id=assignment_id)
        except CourierAssignment.DoesNotExist:
            return

        if assignment.status != AssignmentStatus.OFFERED:
            return  # Allaqachon qabul/rad etilgan

        if not assignment.is_expired:
            return  # Hali muddati o'tmagan

        assignment.status = AssignmentStatus.TIMED_OUT
        assignment.save(update_fields=["status"])

        print(f"[DISPATCH] Offer timed out: {assignment_id}. Reassigning...")
        reassign_or_escalate(assignment.order)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=1)
def trigger_dispatch_for_order(self, order_id: str):
    """
    Checkout tugagandan so'ng checkout service tomonidan chaqiriladi.
    Buyurtma READY_FOR_PICKUP holatiga o'tgandan keyin dispatch boshlanadi.
    """
    try:
        from apps.orders.models import Order
        from apps.orders.constants import OrderStatus
        from apps.dispatch.services import assign_courier_to_order
        from apps.dispatch.exceptions import NoCouriersAvailable

        try:
            order = Order.objects.select_related("branch").get(id=order_id)
        except Order.DoesNotExist:
            return

        if order.status != OrderStatus.READY_FOR_PICKUP:
            return

        try:
            assignment = assign_courier_to_order(order)
            print(f"[DISPATCH] Order {order.public_id} → Courier {assignment.courier}")
        except NoCouriersAvailable:
            print(f"[DISPATCH] No couriers for order {order.public_id}. Escalating...")
            notify_admin_no_courier.delay(order_id)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def notify_admin_no_courier(self, order_id: str):
    """Admin/ops qatoriga buyurtmani yuboradi."""
    try:
        from apps.orders.models import Order
        order = Order.objects.get(id=order_id)
        # TODO: Telegram bot yoki admin dashboard xabarnomasi
        print(f"[DISPATCH] ADMIN ALERT: No courier for order #{order.public_id}")
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def sweep_expired_offers():
    """
    Celery Beat: har 60 soniyada muddati o'tgan offerlarni tozalaydi.
    timeout task muvaffaqiyatsiz bo'lgan holatlar uchun backup.
    """
    from apps.dispatch.selectors import get_expired_offers
    from apps.dispatch.constants import AssignmentStatus
    from apps.dispatch.services import reassign_or_escalate

    expired = get_expired_offers()
    count = 0
    for assignment in expired:
        assignment.status = AssignmentStatus.TIMED_OUT
        assignment.save(update_fields=["status"])
        try:
            reassign_or_escalate(assignment.order)
        except Exception as e:
            print(f"[DISPATCH] sweep reassign error: {e}")
        count += 1

    if count:
        print(f"[DISPATCH] Swept {count} expired offers")
    return count
