"""
apps/notifications/providers/

Provider adapter pattern – same interface for every channel.
New channels (e.g. WhatsApp) only need to implement BaseProvider.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import requests
from django.conf import settings

from apps.notifications.exceptions import (
    ChannelNotConfiguredError,
    InvalidDeviceTokenError,
    PushDeliveryError,
    SMSDeliveryError,
    TelegramDeliveryError,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Data classes                                                        #
# ------------------------------------------------------------------ #

@dataclass
class PushMessage:
    token: str
    title: str
    body: str
    data: dict = field(default_factory=dict)
    image_url: str | None = None


@dataclass
class SMSMessage:
    phone: str           # E.164 format: +998901234567
    text: str


@dataclass
class EmailMessage:
    to: str
    subject: str
    body_html: str
    body_text: str = ""


@dataclass
class TelegramMessage:
    chat_id: str
    text: str
    parse_mode: str = "HTML"


@dataclass
class ProviderResult:
    success: bool
    provider_message_id: str = ""
    raw_response: dict = field(default_factory=dict)
    error: str = ""


# ------------------------------------------------------------------ #
#  Base                                                                #
# ------------------------------------------------------------------ #

class BaseProvider(ABC):
    @abstractmethod
    def send(self, message: Any) -> ProviderResult:
        raise NotImplementedError


# ------------------------------------------------------------------ #
#  FCM Push Provider                                                   #
# ------------------------------------------------------------------ #

class FCMProvider(BaseProvider):
    """
    Firebase Cloud Messaging (v1 HTTP API).
    Requires FIREBASE_SERVER_KEY in settings or GOOGLE_APPLICATION_CREDENTIALS
    for OAuth2-based v1 API.
    """

    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self) -> None:
        self.server_key = getattr(settings, "FCM_SERVER_KEY", None)
        if not self.server_key:
            raise ChannelNotConfiguredError(
                "FCM_SERVER_KEY is not configured.", channel="push"
            )

    def send(self, message: PushMessage) -> ProviderResult:
        payload = {
            "to": message.token,
            "notification": {
                "title": message.title,
                "body": message.body,
            },
            "data": message.data or {},
        }
        if message.image_url:
            payload["notification"]["image"] = message.image_url

        try:
            resp = requests.post(
                self.FCM_URL,
                json=payload,
                headers={
                    "Authorization": f"key={self.server_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            data = resp.json()

            if resp.status_code != 200:
                raise PushDeliveryError(
                    f"FCM HTTP {resp.status_code}: {resp.text}", channel="push"
                )

            # FCM returns 200 even for token errors
            if data.get("failure") == 1:
                error = data.get("results", [{}])[0].get("error", "unknown")
                if error in ("NotRegistered", "InvalidRegistration"):
                    raise InvalidDeviceTokenError(
                        f"FCM token invalid: {error}", channel="push"
                    )
                raise PushDeliveryError(f"FCM error: {error}", channel="push")

            msg_id = data.get("results", [{}])[0].get("message_id", "")
            logger.info("FCM sent: %s → %s", msg_id, message.token[:20])
            return ProviderResult(
                success=True,
                provider_message_id=msg_id,
                raw_response=data,
            )

        except (requests.RequestException,) as exc:
            raise PushDeliveryError(f"FCM network error: {exc}", channel="push") from exc


# ------------------------------------------------------------------ #
#  Eskiz SMS Provider (eskiz.uz – Uzbekistan)                          #
# ------------------------------------------------------------------ #

class EskizSMSProvider(BaseProvider):
    """
    Eskiz.uz SMS gateway – used for OTP and transactional SMS in Uzbekistan.
    Docs: https://documenter.getpostman.com/view/663428/RzfmES4z
    """

    BASE_URL = "https://notify.eskiz.uz/api"

    def __init__(self) -> None:
        self.email = getattr(settings, "ESKIZ_EMAIL", None)
        self.password = getattr(settings, "ESKIZ_PASSWORD", None)
        if not self.email or not self.password:
            raise ChannelNotConfiguredError(
                "ESKIZ_EMAIL or ESKIZ_PASSWORD not configured.", channel="sms"
            )
        self._token: str | None = None

    def _authenticate(self) -> str:
        resp = requests.post(
            f"{self.BASE_URL}/auth/login",
            data={"email": self.email, "password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("token")
        if not token:
            raise SMSDeliveryError("Eskiz auth failed – no token returned.", channel="sms")
        self._token = token
        return token

    def _get_token(self) -> str:
        return self._token or self._authenticate()

    def send(self, message: SMSMessage) -> ProviderResult:
        token = self._get_token()
        from_name = getattr(settings, "ESKIZ_FROM", "4546")
        payload = {
            "mobile_phone": message.phone.lstrip("+"),
            "message": message.text,
            "from": from_name,
        }
        try:
            resp = requests.post(
                f"{self.BASE_URL}/message/sms/send",
                data=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )

            # Refresh token and retry once if expired
            if resp.status_code == 401:
                self._token = None
                token = self._authenticate()
                resp = requests.post(
                    f"{self.BASE_URL}/message/sms/send",
                    data=payload,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )

            data = resp.json()
            if data.get("status") != "waiting":
                raise SMSDeliveryError(
                    f"Eskiz send failed: {data.get('message', resp.text)}", channel="sms"
                )

            msg_id = str(data.get("id", ""))
            logger.info("Eskiz SMS sent: %s → %s", msg_id, message.phone)
            return ProviderResult(
                success=True,
                provider_message_id=msg_id,
                raw_response=data,
            )

        except (requests.RequestException,) as exc:
            raise SMSDeliveryError(f"Eskiz network error: {exc}", channel="sms") from exc


# ------------------------------------------------------------------ #
#  PlayMobile SMS Provider (backup)                                    #
# ------------------------------------------------------------------ #

class PlayMobileSMSProvider(BaseProvider):
    """
    PlayMobile SMS gateway – alternative to Eskiz.
    """

    BASE_URL = "http://91.204.239.44/broker-api/send"

    def __init__(self) -> None:
        self.username = getattr(settings, "PLAYMOBILE_USERNAME", None)
        self.password = getattr(settings, "PLAYMOBILE_PASSWORD", None)
        self.originator = getattr(settings, "PLAYMOBILE_ORIGINATOR", "GlovoUZ")
        if not self.username or not self.password:
            raise ChannelNotConfiguredError(
                "PLAYMOBILE_USERNAME or PLAYMOBILE_PASSWORD not configured.", channel="sms"
            )

    def send(self, message: SMSMessage) -> ProviderResult:
        import uuid as _uuid

        payload = {
            "messages": [
                {
                    "recipient": message.phone.lstrip("+"),
                    "message-id": str(_uuid.uuid4()),
                    "sms": {
                        "originator": self.originator,
                        "content": {"text": message.text},
                    },
                }
            ]
        }
        try:
            resp = requests.post(
                self.BASE_URL,
                json=payload,
                auth=(self.username, self.password),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("PlayMobile SMS sent to %s", message.phone)
            return ProviderResult(success=True, raw_response=data)

        except requests.RequestException as exc:
            raise SMSDeliveryError(
                f"PlayMobile network error: {exc}", channel="sms"
            ) from exc


# ------------------------------------------------------------------ #
#  Email Provider (Django SMTP)                                        #
# ------------------------------------------------------------------ #

class DjangoEmailProvider(BaseProvider):
    """Uses Django's built-in email backend (SMTP/SES etc.)."""

    def send(self, message: EmailMessage) -> ProviderResult:
        from django.core.mail import EmailMultiAlternatives

        try:
            email = EmailMultiAlternatives(
                subject=message.subject,
                body=message.body_text or message.body_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[message.to],
            )
            if message.body_html:
                email.attach_alternative(message.body_html, "text/html")
            email.send(fail_silently=False)
            logger.info("Email sent to %s", message.to)
            return ProviderResult(success=True)
        except Exception as exc:
            from apps.notifications.exceptions import EmailDeliveryError
            raise EmailDeliveryError(f"Email send failed: {exc}", channel="email") from exc


# ------------------------------------------------------------------ #
#  Telegram Admin Alert Provider                                       #
# ------------------------------------------------------------------ #

class TelegramProvider(BaseProvider):
    """
    Sends admin/ops alerts to a Telegram chat via Bot API.
    Use for MERCHANT_NEW_ORDER, MERCHANT_ORDER_TIMEOUT, etc.
    """

    def __init__(self) -> None:
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.default_chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)
        if not self.bot_token:
            raise ChannelNotConfiguredError(
                "TELEGRAM_BOT_TOKEN not configured.", channel="telegram"
            )

    def send(self, message: TelegramMessage) -> ProviderResult:
        chat_id = message.chat_id or self.default_chat_id
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message.text,
            "parse_mode": message.parse_mode,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if not data.get("ok"):
                raise TelegramDeliveryError(
                    f"Telegram error: {data.get('description', resp.text)}", channel="telegram"
                )
            msg_id = str(data.get("result", {}).get("message_id", ""))
            return ProviderResult(success=True, provider_message_id=msg_id, raw_response=data)
        except requests.RequestException as exc:
            raise TelegramDeliveryError(
                f"Telegram network error: {exc}", channel="telegram"
            ) from exc


# ------------------------------------------------------------------ #
#  Provider factory                                                    #
# ------------------------------------------------------------------ #

def get_push_provider() -> FCMProvider:
    return FCMProvider()


def get_sms_provider() -> BaseProvider:
    """Returns preferred SMS provider based on settings."""
    preferred = getattr(settings, "SMS_PROVIDER", "eskiz")
    if preferred == "playmobile":
        return PlayMobileSMSProvider()
    return EskizSMSProvider()


def get_email_provider() -> DjangoEmailProvider:
    return DjangoEmailProvider()


def get_telegram_provider() -> TelegramProvider:
    return TelegramProvider()
