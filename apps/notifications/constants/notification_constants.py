from django.db import models


class NotificationChannel(models.TextChoices):
    PUSH = "push", "Push Notification"
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    IN_APP = "in_app", "In-App"
    TELEGRAM = "telegram", "Telegram (Admin)"


class NotificationEvent(models.TextChoices):
    # Order lifecycle
    ORDER_CREATED = "order_created", "Order Created"
    ORDER_MERCHANT_CONFIRMED = "order_merchant_confirmed", "Merchant Confirmed"
    ORDER_PREPARING = "order_preparing", "Preparing"
    ORDER_READY_FOR_PICKUP = "order_ready_for_pickup", "Ready for Pickup"
    ORDER_COURIER_ASSIGNED = "order_courier_assigned", "Courier Assigned"
    ORDER_PICKED_UP = "order_picked_up", "Picked Up"
    ORDER_ON_THE_WAY = "order_on_the_way", "On the Way"
    ORDER_DELIVERED = "order_delivered", "Delivered"
    ORDER_CANCELLED = "order_cancelled", "Order Cancelled"

    # Payment events
    PAYMENT_RECEIVED = "payment_received", "Payment Received"
    REFUND_CREATED = "refund_created", "Refund Created"
    REFUND_COMPLETED = "refund_completed", "Refund Completed"

    # Courier events
    COURIER_NEW_ORDER_OFFER = "courier_new_order_offer", "New Order Offer"
    COURIER_ORDER_OFFER_EXPIRED = "courier_order_offer_expired", "Order Offer Expired"

    # Merchant events
    MERCHANT_NEW_ORDER = "merchant_new_order", "New Order for Merchant"
    MERCHANT_ORDER_TIMEOUT = "merchant_order_timeout", "Order Confirmation Timeout"

    # Account events
    ACCOUNT_VERIFIED = "account_verified", "Account Verified"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"  # User opted out or channel not applicable


class NotificationType(models.TextChoices):
    TRANSACTIONAL = "transactional", "Transactional"
    PROMOTIONAL = "promotional", "Promotional"
    SYSTEM = "system", "System"


class SMSProvider(models.TextChoices):
    ESKIZ = "eskiz", "Eskiz.uz"
    PLAYMOBILE = "playmobile", "PlayMobile"


class PushProvider(models.TextChoices):
    FCM = "fcm", "Firebase Cloud Messaging"
    APNS = "apns", "Apple Push Notification Service"


# ------------------------------------------------------------------ #
#  Event → channel mapping                                            #
#  Defines which channels fire for each event                         #
# ------------------------------------------------------------------ #
NOTIFICATION_EVENT_CHANNELS: dict[str, list[str]] = {
    NotificationEvent.ORDER_CREATED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
        NotificationChannel.SMS,
    ],
    NotificationEvent.ORDER_MERCHANT_CONFIRMED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.ORDER_PREPARING: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.ORDER_READY_FOR_PICKUP: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.ORDER_COURIER_ASSIGNED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.ORDER_PICKED_UP: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.ORDER_ON_THE_WAY: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.ORDER_DELIVERED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
        NotificationChannel.SMS,
    ],
    NotificationEvent.ORDER_CANCELLED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
        NotificationChannel.SMS,
    ],
    NotificationEvent.PAYMENT_RECEIVED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.REFUND_CREATED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
        NotificationChannel.SMS,
    ],
    NotificationEvent.REFUND_COMPLETED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
        NotificationChannel.SMS,
    ],
    NotificationEvent.COURIER_NEW_ORDER_OFFER: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.COURIER_ORDER_OFFER_EXPIRED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
    NotificationEvent.MERCHANT_NEW_ORDER: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
        NotificationChannel.TELEGRAM,
    ],
    NotificationEvent.MERCHANT_ORDER_TIMEOUT: [
        NotificationChannel.PUSH,
        NotificationChannel.TELEGRAM,
    ],
    NotificationEvent.ACCOUNT_VERIFIED: [
        NotificationChannel.PUSH,
        NotificationChannel.IN_APP,
    ],
}

# ------------------------------------------------------------------ #
#  Event → message templates (uz/ru)                                  #
# ------------------------------------------------------------------ #
NOTIFICATION_EVENT_TEMPLATES: dict[str, dict] = {
    NotificationEvent.ORDER_CREATED: {
        "title_uz": "Buyurtma qabul qilindi",
        "title_ru": "Заказ принят",
        "body_uz": "#{order_id} raqamli buyurtmangiz qabul qilindi. Summa: {total} so'm",
        "body_ru": "Ваш заказ #{order_id} принят. Сумма: {total} сум",
    },
    NotificationEvent.ORDER_MERCHANT_CONFIRMED: {
        "title_uz": "Buyurtma tasdiqlandi",
        "title_ru": "Заказ подтверждён",
        "body_uz": "#{order_id} buyurtmangizni restoran tasdiqiladi va tayyorlashni boshladi.",
        "body_ru": "Заказ #{order_id} подтверждён и начинается приготовление.",
    },
    NotificationEvent.ORDER_PREPARING: {
        "title_uz": "Tayyorlanmoqda",
        "title_ru": "Готовится",
        "body_uz": "#{order_id} buyurtmangiz tayyorlanmoqda.",
        "body_ru": "Ваш заказ #{order_id} готовится.",
    },
    NotificationEvent.ORDER_READY_FOR_PICKUP: {
        "title_uz": "Tayyor!",
        "title_ru": "Готово!",
        "body_uz": "#{order_id} buyurtmangiz kuryerni kutmoqda.",
        "body_ru": "Заказ #{order_id} готов, ожидает курьера.",
    },
    NotificationEvent.ORDER_COURIER_ASSIGNED: {
        "title_uz": "Kuryer yo'lda",
        "title_ru": "Курьер в пути",
        "body_uz": "{courier_name} buyurtmangizni olib keladi.",
        "body_ru": "{courier_name} доставит ваш заказ.",
    },
    NotificationEvent.ORDER_PICKED_UP: {
        "title_uz": "Kuryer oldi",
        "title_ru": "Курьер забрал заказ",
        "body_uz": "Kuryer buyurtmangizni oldi. Yetkazish vaqti: ~{eta} daqiqa.",
        "body_ru": "Курьер забрал заказ. Время доставки: ~{eta} мин.",
    },
    NotificationEvent.ORDER_ON_THE_WAY: {
        "title_uz": "Yetib kelmoqda",
        "title_ru": "Едет к вам",
        "body_uz": "Kuryer sizga yetib kelmoqda.",
        "body_ru": "Курьер едет к вам.",
    },
    NotificationEvent.ORDER_DELIVERED: {
        "title_uz": "Yetkazildi! 🎉",
        "title_ru": "Доставлено! 🎉",
        "body_uz": "#{order_id} buyurtmangiz yetkazildi. Rahmat!",
        "body_ru": "Заказ #{order_id} доставлен. Приятного аппетита!",
    },
    NotificationEvent.ORDER_CANCELLED: {
        "title_uz": "Buyurtma bekor qilindi",
        "title_ru": "Заказ отменён",
        "body_uz": "#{order_id} buyurtmangiz bekor qilindi. Sabab: {reason}",
        "body_ru": "Заказ #{order_id} отменён. Причина: {reason}",
    },
    NotificationEvent.PAYMENT_RECEIVED: {
        "title_uz": "To'lov qabul qilindi",
        "title_ru": "Оплата получена",
        "body_uz": "{amount} so'm to'lov qabul qilindi.",
        "body_ru": "Получена оплата {amount} сум.",
    },
    NotificationEvent.REFUND_CREATED: {
        "title_uz": "Qaytarish boshlandi",
        "title_ru": "Возврат инициирован",
        "body_uz": "{amount} so'm qaytarish jarayoni boshlandi.",
        "body_ru": "Начат процесс возврата {amount} сум.",
    },
    NotificationEvent.REFUND_COMPLETED: {
        "title_uz": "Pul qaytarildi",
        "title_ru": "Деньги возвращены",
        "body_uz": "{amount} so'm hisobingizga qaytarildi.",
        "body_ru": "{amount} сум возвращены на ваш счёт.",
    },
    NotificationEvent.COURIER_NEW_ORDER_OFFER: {
        "title_uz": "Yangi buyurtma!",
        "title_ru": "Новый заказ!",
        "body_uz": "{merchant_name} — {distance} km. {amount} so'm. Qabul qilasizmi?",
        "body_ru": "{merchant_name} — {distance} км. {amount} сум. Принять?",
    },
    NotificationEvent.MERCHANT_NEW_ORDER: {
        "title_uz": "Yangi buyurtma!",
        "title_ru": "Новый заказ!",
        "body_uz": "#{order_id} yangi buyurtma keldi. Jami: {total} so'm.",
        "body_ru": "Новый заказ #{order_id}. Итого: {total} сум.",
    },
}
