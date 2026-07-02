"""
apps/notifications/api/views.py

Thin views – all logic delegated to services/selectors.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.api.serializers import (
    DeviceTokenRegisterSerializer,
    DeviceTokenSerializer,
    MarkReadSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
    UnreadCountSerializer,
)
from apps.notifications.selectors import (
    get_notifications_for_user,
    get_unread_in_app_count,
)
from apps.notifications.services import (
    DeviceTokenService,
    NotificationPreferenceService,
    NotificationService,
)


# ------------------------------------------------------------------ #
#  Device Tokens                                                       #
# ------------------------------------------------------------------ #

class DeviceTokenRegisterView(APIView):
    """
    POST /api/v1/notifications/device-tokens/
    Register or update a push token for the current user's device.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        device = DeviceTokenService.register(
            user_id=request.user.pk,
            token=d["token"],
            provider=d["provider"],
            device_id=d.get("device_id", ""),
            device_name=d.get("device_name", ""),
            app_version=d.get("app_version", ""),
        )
        return Response(DeviceTokenSerializer(device).data, status=status.HTTP_201_CREATED)


class DeviceTokenDeregisterView(APIView):
    """
    DELETE /api/v1/notifications/device-tokens/{token}/
    Deregister a push token (e.g. on logout).
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, token: str):
        DeviceTokenService.deregister(token)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ #
#  Notification Preferences                                            #
# ------------------------------------------------------------------ #

class NotificationPreferenceView(APIView):
    """
    GET  /api/v1/notifications/preferences/
    PATCH /api/v1/notifications/preferences/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.notifications.selectors import get_or_create_notification_preference
        pref = get_or_create_notification_preference(request.user.pk)
        return Response(NotificationPreferenceSerializer(pref).data)

    def patch(self, request):
        serializer = NotificationPreferenceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        pref = NotificationPreferenceService.update(
            user_id=request.user.pk,
            **serializer.validated_data,
        )
        return Response(NotificationPreferenceSerializer(pref).data)


# ------------------------------------------------------------------ #
#  In-App Notification Feed                                            #
# ------------------------------------------------------------------ #

class NotificationListView(APIView):
    """
    GET /api/v1/notifications/
    Returns paginated in-app notification feed.
    Query params:
        unread_only=true
        limit=50  (max 100)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.notifications.constants import NotificationChannel

        unread_only = request.query_params.get("unread_only", "").lower() == "true"
        limit = min(int(request.query_params.get("limit", 50)), 100)

        notifications = get_notifications_for_user(
            user_id=request.user.pk,
            channel=NotificationChannel.IN_APP,
            unread_only=unread_only,
            limit=limit,
        )
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationUnreadCountView(APIView):
    """
    GET /api/v1/notifications/unread-count/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = get_unread_in_app_count(request.user.pk)
        return Response(UnreadCountSerializer({"unread_count": count}).data)


class NotificationMarkReadView(APIView):
    """
    POST /api/v1/notifications/mark-read/
    Body: { "notification_id": "<uuid>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success = NotificationService.mark_read(
            notification_id=serializer.validated_data["notification_id"],
            user_id=request.user.pk,
        )
        return Response({"success": success})


class NotificationMarkAllReadView(APIView):
    """
    POST /api/v1/notifications/mark-all-read/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_read(request.user.pk)
        return Response({"marked": count})
