"""
Kuryer tayinlash xizmati — asosiy dispatch algoritmi.

Mantiq (Uber / Bolt / Glovo uslubida):
1. Har doim ENG YAQIN bo'sh kuryerga (bittasiga) taklif yuboriladi —
   radius bo'yicha kuryerlar ro'yxatidan tanlash emas.
2. Kuryerga OFFER_TIMEOUT_SECONDS (10s) davomida signal/notification boradi.
3. Agar kuryer shu vaqt ichida rad etsa yoki javob bermasa (timeout),
   buyurtma "pending" — ya'ni kuryer kutish holatida qoladi.
4. PENDING_RETRY_SECONDS (5 daqiqa)dan so'ng navbatdagi eng yaqin
   (avval taklif qilinmagan) kuryerga qayta taklif yuboriladi.
5. MAX_ASSIGNMENT_ATTEMPTS marta urinishdan keyin admin/ops qatoriga
   eskalatsiya qilinadi.
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.dispatch.models import CourierAssignment
from apps.dispatch.constants import (
    AssignmentStatus,
    OFFER_TIMEOUT_SECONDS,
    PENDING_RETRY_SECONDS,
    MAX_ASSIGNMENT_ATTEMPTS,
)
from apps.dispatch.selectors import get_nearest_available_courier, count_assignment_attempts
from apps.dispatch.exceptions import NoCouriersAvailable, MaxAttemptsReached


@transaction.atomic
def assign_courier_to_order(order, attempt_number: int = None) -> CourierAssignment:
    """
    Buyurtma uchun ENG YAQIN bo'sh kuryerni topadi va unga taklif yaratadi.

    1. Filialga eng yaqin onlayn kuryerni tanlaydi (avval taklif qilingan/
       rad etgan kuryerlarni chetlab o'tib)
    2. Yangi CourierAssignment (status=OFFERED) yaratadi
    3. Kuryerga WebSocket orqali buyurtma taklifini (notification signal) yuboradi
    4. Celery task bilan OFFER_TIMEOUT_SECONDS (10s) countdown ni ishga tushiradi
    """
    branch = order.branch

    if attempt_number is None:
        attempt_number = count_assignment_attempts(order) + 1

    if attempt_number > MAX_ASSIGNMENT_ATTEMPTS:
        raise MaxAttemptsReached(
            f"Order {order.public_id} uchun {MAX_ASSIGNMENT_ATTEMPTS} ta urinishdan keyin kuryer topilmadi."
        )

    # Bu order uchun ilgari taklif qilingan (rad etgan yoki vaqt tugagan) kuryerlar
    excluded_courier_ids = set(
        CourierAssignment.objects.filter(
            order=order,
            status__in=[AssignmentStatus.REJECTED, AssignmentStatus.TIMED_OUT],
        ).values_list("courier_id", flat=True)
    )

    nearest = get_nearest_available_courier(branch, exclude_courier_ids=excluded_courier_ids)

    if nearest is None:
        raise NoCouriersAvailable()

    chosen = nearest["courier_user"]
    chosen_distance = nearest["distance_km"]

    offer_expires = timezone.now() + timedelta(seconds=OFFER_TIMEOUT_SECONDS)

    assignment = CourierAssignment.objects.create(
        order=order,
        courier=chosen,
        status=AssignmentStatus.OFFERED,
        attempt_number=attempt_number,
        offer_expires_at=offer_expires,
        distance_km=chosen_distance,
    )

    # Kuryerga WebSocket orqali notification signal yuborish
    try:
        from apps.dispatch.services.realtime import send_order_offer_to_courier
        send_order_offer_to_courier(assignment=assignment)
    except Exception:
        pass

    # 10 soniyalik timeout task ni ishga tushirish
    try:
        from apps.dispatch.tasks import handle_offer_timeout
        handle_offer_timeout.apply_async(
            args=[str(assignment.id)],
            countdown=OFFER_TIMEOUT_SECONDS + 1,
        )
    except Exception:
        pass

    return assignment


def reassign_or_escalate(order) -> None:
    """
    Taklif muvaffaqiyatsiz bo'lganda (rad etish / 10s timeout) chaqiriladi.

    Darhol keyingi kuryerga o'tmaydi — buning o'rniga buyurtmani
    "pending" (kuryer kutilmoqda) holatida qoldirib, PENDING_RETRY_SECONDS
    (5 daqiqa)dan keyin qayta urinish uchun Celery task rejalashtiradi.
    Urinishlar soni limitiga yetsa — admin/ops qatoriga eskalatsiya qiladi.
    """
    attempts = count_assignment_attempts(order)
    if attempts >= MAX_ASSIGNMENT_ATTEMPTS:
        _escalate_to_admin(order)
        return

    # Oldindan yaqin atrofda hech kim topilmasa ham darhol tekshirib ko'ramiz —
    # topilmasa ham xafa bo'lmaymiz, baribir 5 daqiqadan keyin qayta uriniladi.
    print(
        f"[DISPATCH] PENDING: Order {order.public_id} kuryer kutmoqda, "
        f"{PENDING_RETRY_SECONDS}s dan keyin qayta taklif qilinadi."
    )

    try:
        from apps.dispatch.tasks import retry_pending_dispatch
        retry_pending_dispatch.apply_async(
            args=[str(order.id)],
            countdown=PENDING_RETRY_SECONDS,
        )
    except Exception as e:
        print(f"[DISPATCH] retry scheduling error: {e}")


def _escalate_to_admin(order):
    """Admin qatoriga yuborish va bildirishnoma."""
    print(f"[DISPATCH] ESCALATE: Order {order.public_id} adminlarga yuborildi")
    try:
        from apps.dispatch.tasks import notify_admin_no_courier
        notify_admin_no_courier.delay(str(order.id))
    except Exception:
        pass
