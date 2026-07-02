from rest_framework import serializers

from apps.notifications.models import DeviceToken, Notification, NotificationPreference
from apps.notifications.constants import NotificationChannel, PushProvider


class DeviceTokenRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=500)
    provider = serializers.ChoiceField(
        choices=PushProvider.choices,
        default=PushProvider.FCM,
    )
    device_id = serializers.CharField(max_length=255, required=False, default="")
    device_name = serializers.CharField(max_length=255, required=False, default="")
    app_version = serializers.CharField(max_length=50, required=False, default="")


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "provider", "device_id", "device_name", "app_version", "is_active", "registered_at"]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "push_enabled",
            "sms_enabled",
            "email_enabled",
            "in_app_enabled",
            "promotional_push",
            "promotional_sms",
            "promotional_email",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "event",
            "channel",
            "notification_type",
            "title",
            "body",
            "data",
            "status",
            "order_id",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields


class MarkReadSerializer(serializers.Serializer):
    notification_id = serializers.UUIDField()


class UnreadCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
