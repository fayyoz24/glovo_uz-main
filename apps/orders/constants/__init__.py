from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    MERCHANT_CONFIRMED = "merchant_confirmed", "Restoran tasdiqladi"
    PREPARING = "preparing", "Tayyorlanmoqda"
    READY_FOR_PICKUP = "ready_for_pickup", "Yetkazib beruvchi uchun tayyor"
    COURIER_ASSIGNED = "courier_assigned", "Kuryer belgilandi"
    PICKED_UP = "picked_up", "Kuryer oldi"
    ON_THE_WAY = "on_the_way", "Yo'lda"
    DELIVERED = "delivered", "Yetkazib berildi"
    CANCELLED = "cancelled", "Bekor qilindi"

    @classmethod
    def cancellable_statuses(cls):
        return [cls.PENDING, cls.MERCHANT_CONFIRMED, cls.PREPARING]

    @classmethod
    def transitions(cls):
        """Ruxsat etilgan holat o'tishlari."""
        return {
            cls.PENDING: [cls.MERCHANT_CONFIRMED, cls.CANCELLED],
            cls.MERCHANT_CONFIRMED: [cls.PREPARING, cls.CANCELLED],
            cls.PREPARING: [cls.READY_FOR_PICKUP, cls.CANCELLED],
            cls.READY_FOR_PICKUP: [cls.COURIER_ASSIGNED],
            cls.COURIER_ASSIGNED: [cls.PICKED_UP],
            cls.PICKED_UP: [cls.ON_THE_WAY],
            cls.ON_THE_WAY: [cls.DELIVERED],
            cls.DELIVERED: [],
            cls.CANCELLED: [],
        }


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Naqd pul"
    CLICK = "click", "Click"
    PAYME = "payme", "Payme"
    UZCARD = "uzcard", "Uzcard"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    PAID = "paid", "To'landi"
    FAILED = "failed", "Muvaffaqiyatsiz"
    REFUNDED = "refunded", "Qaytarildi"
    PARTIALLY_REFUNDED = "partially_refunded", "Qisman qaytarildi"


class CancelReason(models.TextChoices):
    CUSTOMER_REQUEST = "customer_request", "Mijoz so'rovi"
    MERCHANT_REJECTED = "merchant_rejected", "Restoran rad etdi"
    NO_COURIER = "no_courier", "Kuryer topilmadi"
    PAYMENT_FAILED = "payment_failed", "To'lov muvaffaqiyatsiz"
    TIMEOUT = "timeout", "Vaqt tugadi"
    OTHER = "other", "Boshqa"
