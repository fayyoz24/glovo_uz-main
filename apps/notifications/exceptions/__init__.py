class NotificationError(Exception):
    """Base notification error."""

    def __init__(self, message: str, channel: str | None = None):
        self.channel = channel
        super().__init__(message)


class PushDeliveryError(NotificationError):
    """FCM/APNS push send failure."""


class SMSDeliveryError(NotificationError):
    """SMS provider send failure."""


class EmailDeliveryError(NotificationError):
    """Email send failure."""


class TelegramDeliveryError(NotificationError):
    """Telegram send failure."""


class InvalidDeviceTokenError(NotificationError):
    """Device token is invalid or expired; should be deregistered."""


class TemplateRenderError(NotificationError):
    """Notification template rendering failure."""


class ChannelNotConfiguredError(NotificationError):
    """Required provider credentials not configured."""


class NotificationOptedOutError(NotificationError):
    """User has opted out of this notification channel/type."""
