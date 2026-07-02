import uuid

from django.conf import settings
from django.db import models

from apps.notifications.constants import (
    NotificationChannel,
    NotificationEvent,
    NotificationStatus,
    NotificationType,
    PushProvider,
)


class DeviceToken(models.Model):
    """
    Stores FCM/APNS device push tokens per user per device.
    A user can have multiple devices (phone + tablet, iOS + Android).
    Tokens are deregistered on InvalidDeviceTokenError from provider.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_device_tokens"
    )
    token = models.TextField()
    provider = models.CharField(
        max_length=20,
        choices=PushProvider.choices,
        default=PushProvider.FCM,
    )
    device_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Unique device identifier (e.g. Android ID or iOS identifierForVendor)",
    )
    device_name = models.CharField(max_length=255, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification_device_tokens"
        unique_together = [("user", "device_id", "provider")]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"DeviceToken({self.user_id}, {self.provider}, active={self.is_active})"


class NotificationPreference(models.Model):
    """
    Per-user opt-in / opt-out settings per channel and event type.
    Transactional events (OTP, order status) cannot be fully disabled.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )

    # Channel-level opt-outs
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)

    # Granular event-level opt-outs (promotional / non-critical)
    promotional_push = models.BooleanField(default=True)
    promotional_sms = models.BooleanField(default=False)
    promotional_email = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"NotificationPreference({self.user_id})"

    def is_channel_enabled(self, channel: str, ntype: str) -> bool:
        """
        Returns True if the user allows this channel/type combination.
        Transactional notifications always go through.
        """
        if ntype == NotificationType.TRANSACTIONAL:
            return True  # can't opt out of OTP, order status etc.

        if channel == NotificationChannel.PUSH:
            return self.push_enabled and (
                self.promotional_push if ntype == NotificationType.PROMOTIONAL else True
            )
        if channel == NotificationChannel.SMS:
            return self.sms_enabled and (
                self.promotional_sms if ntype == NotificationType.PROMOTIONAL else True
            )
        if channel == NotificationChannel.EMAIL:
            return self.email_enabled and (
                self.promotional_email if ntype == NotificationType.PROMOTIONAL else True
            )
        if channel == NotificationChannel.IN_APP:
            return self.in_app_enabled
        return True


class Notification(models.Model):
    """
    Immutable audit log of every notification attempt.
    One row per channel per dispatch attempt.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="notifications",
    )

    # Classification
    event = models.CharField(max_length=60, choices=NotificationEvent.choices)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.TRANSACTIONAL,
    )

    # Content
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True, help_text="Extra payload for deep-linking")

    # Target identifiers (channel-specific)
    push_token = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email_address = models.EmailField(blank=True)

    # Delivery
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    failure_reason = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)

    # Related objects (nullable – notification may outlive the order)
    order_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Retry tracking
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["recipient", "channel", "status"]),
            models.Index(fields=["recipient", "event", "created_at"]),
            models.Index(fields=["status", "attempt_count"]),
            models.Index(fields=["order_id"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification({self.event}, {self.channel}, {self.status})"

    @property
    def is_retriable(self) -> bool:
        return (
            self.status == NotificationStatus.FAILED
            and self.attempt_count < self.max_attempts
        )

    @property
    def is_read(self) -> bool:
        return self.read_at is not None
