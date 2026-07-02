[text](../glovo_uz_fixed/telegram_bot)# Notifications App – Integration Guide

## 1. Project Structure

```
apps/notifications/
├── __init__.py
├── apps.py
├── constants/
│   ├── __init__.py
│   └── notification_constants.py   # Enums, templates, channel mappings
├── exceptions/
│   └── __init__.py                 # NotificationError hierarchy
├── models/
│   ├── __init__.py
│   └── notification.py             # Notification, DeviceToken, NotificationPreference
├── providers.py                    # FCM, Eskiz SMS, PlayMobile, Email, Telegram adapters
├── selectors/
│   └── __init__.py                 # Read-only DB queries
├── services/
│   └── __init__.py                 # NotificationService, DeviceTokenService
├── tasks.py                        # Celery tasks (called by other apps)
├── consumers/
│   └── __init__.py                 # WebSocket consumer (Django Channels)
├── permissions/
│   └── __init__.py
├── api/
│   ├── __init__.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── migrations/
    ├── __init__.py
    └── 0001_initial.py
```

---

## 2. Settings Required

```python
# config/settings/base.py

INSTALLED_APPS = [
    ...
    "channels",
    "apps.notifications",
]

# Channels
ASGI_APPLICATION = "config.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("redis", 6379)]},
    }
}

# FCM
FCM_SERVER_KEY = env("FCM_SERVER_KEY")

# SMS (choose one)
SMS_PROVIDER = "eskiz"  # or "playmobile"
ESKIZ_EMAIL = env("ESKIZ_EMAIL")
ESKIZ_PASSWORD = env("ESKIZ_PASSWORD")
ESKIZ_FROM = "4546"  # or your sender name

# Telegram admin alerts
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = env("TELEGRAM_ADMIN_CHAT_ID")

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@glovo.uz"
```

---

## 3. URL Registration

```python
# config/urls.py
urlpatterns = [
    ...
    path("api/v1/notifications/", include("apps.notifications.api.urls")),
]
```

---

## 4. WebSocket Routing (Django Channels)

```python
# config/routing.py
from django.urls import path
from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]

# config/asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

---

## 5. Celery Beat Schedule

```python
# config/celery.py
app.conf.beat_schedule = {
    "retry-failed-notifications": {
        "task": "notifications.retry_failed_notifications",
        "schedule": crontab(minute="*/10"),
    },
    "cleanup-old-notifications": {
        "task": "notifications.cleanup_old_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
}
```

---

## 6. How Other Apps Trigger Notifications

### orders/services.py → order placed
```python
from apps.notifications.tasks import send_order_created, send_merchant_new_order

# Inside OrderService.checkout():
send_order_created.delay(
    order_id=str(order.id),
    customer_id=order.customer_id,
    context={"order_id": order.public_id, "total": str(order.total_amount)},
)
send_merchant_new_order.delay(
    order_id=str(order.id),
    merchant_owner_id=branch.merchant.owner_id,
    context={"order_id": order.public_id, "total": str(order.total_amount)},
)
```

### orders/services.py → status changed
```python
from apps.notifications.tasks import send_order_status_changed
from apps.notifications.constants import NotificationEvent

EVENT_MAP = {
    "merchant_confirmed": NotificationEvent.ORDER_MERCHANT_CONFIRMED,
    "preparing":          NotificationEvent.ORDER_PREPARING,
    "ready_for_pickup":   NotificationEvent.ORDER_READY_FOR_PICKUP,
    "courier_assigned":   NotificationEvent.ORDER_COURIER_ASSIGNED,
    "picked_up":          NotificationEvent.ORDER_PICKED_UP,
    "on_the_way":         NotificationEvent.ORDER_ON_THE_WAY,
    "delivered":          NotificationEvent.ORDER_DELIVERED,
    "cancelled":          NotificationEvent.ORDER_CANCELLED,
}

event = EVENT_MAP.get(new_status)
if event:
    send_order_status_changed.delay(
        order_id=str(order.id),
        customer_id=order.customer_id,
        event=event,
        context={"order_id": order.public_id, "reason": cancel_reason or ""},
    )
```

### dispatch/services.py → courier offer
```python
from apps.notifications.tasks import send_courier_order_offer

send_courier_order_offer.delay(
    order_id=str(order.id),
    courier_user_id=courier.user_id,
    context={
        "merchant_name": order.branch.merchant.name,
        "distance": "1.2",
        "amount": str(order.total_amount),
    },
)
```

### payments/services.py → payment/refund events
```python
from apps.notifications.tasks import send_payment_notification
from apps.notifications.constants import NotificationEvent

send_payment_notification.delay(
    event=NotificationEvent.PAYMENT_RECEIVED,
    customer_id=order.customer_id,
    context={"amount": str(transaction.amount)},
    order_id=str(order.id),
)
```

### accounts/services.py → OTP
```python
from apps.notifications.tasks import send_otp_sms

send_otp_sms.delay(phone="+998901234567", code="123456", lang="uz")
```

---

## 7. REST API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/v1/notifications/device-tokens/` | Register push token |
| DELETE | `/api/v1/notifications/device-tokens/{token}/` | Deregister token |
| GET | `/api/v1/notifications/preferences/` | Get preferences |
| PATCH | `/api/v1/notifications/preferences/` | Update preferences |
| GET | `/api/v1/notifications/` | In-app notification feed |
| GET | `/api/v1/notifications/unread-count/` | Unread badge count |
| POST | `/api/v1/notifications/mark-read/` | Mark one as read |
| POST | `/api/v1/notifications/mark-all-read/` | Mark all as read |

---

## 8. WebSocket Client (JavaScript)

```javascript
const ws = new WebSocket(`wss://api.glovo.uz/ws/notifications/?token=${jwtToken}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "new_notification") {
        showToast(data.notification.title, data.notification.body);
        updateBadge(data.unread_count);
    }
};

// Mark as read
ws.send(JSON.stringify({
    action: "mark_read",
    notification_id: "uuid-here"
}));

// Mark all read
ws.send(JSON.stringify({ action: "mark_all_read" }));
```

---

## 9. Adding a New Notification Event

1. Add event to `NotificationEvent` in `constants/notification_constants.py`
2. Add channel list to `NOTIFICATION_EVENT_CHANNELS`
3. Add uz/ru templates to `NOTIFICATION_EVENT_TEMPLATES`
4. Create a Celery task in `tasks.py`
5. Call the task from the relevant service (orders, payments, etc.)

No changes needed in views, serializers, or services — they are event-agnostic.
