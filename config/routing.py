from django.urls import path, re_path

from apps.dispatch.consumers import CourierConsumer, OrderTrackingConsumer
from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/courier/$", CourierConsumer.as_asgi()),
    re_path(r"ws/orders/(?P<order_id>[0-9a-f-]+)/$", OrderTrackingConsumer.as_asgi()),
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]
