from django.urls import path

from apps.notifications.api.views import (
    DeviceTokenDeregisterView,
    DeviceTokenRegisterView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationPreferenceView,
    NotificationUnreadCountView,
)

app_name = "notifications"

urlpatterns = [
    # Push device tokens
    path(
        "device-tokens/",
        DeviceTokenRegisterView.as_view(),
        name="device-token-register",
    ),
    path(
        "device-tokens/<str:token>/",
        DeviceTokenDeregisterView.as_view(),
        name="device-token-deregister",
    ),

    # Preferences
    path(
        "preferences/",
        NotificationPreferenceView.as_view(),
        name="preferences",
    ),

    # In-app feed
    path(
        "",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "unread-count/",
        NotificationUnreadCountView.as_view(),
        name="unread-count",
    ),
    path(
        "mark-read/",
        NotificationMarkReadView.as_view(),
        name="mark-read",
    ),
    path(
        "mark-all-read/",
        NotificationMarkAllReadView.as_view(),
        name="mark-all-read",
    ),
]
