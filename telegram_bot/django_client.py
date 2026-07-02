"""
telegram_bot/django_client.py

Bot Django backend bilan shu modul orqali gaplashadi.
Barcha HTTP so'rovlar bu yerda — handlers clean bo'lsin.
"""
from __future__ import annotations

import logging
from typing import Optional, TypedDict

import requests

from telegram_bot.config import BACKEND_BASE_URL, BOT_SHARED_SECRET

logger = logging.getLogger(__name__)

BASE = BACKEND_BASE_URL.rstrip("/")
HEADERS = {
    "Content-Type": "application/json",
    "X-Telegram-Bot-Api-Secret-Token": BOT_SHARED_SECRET,
}


class LoginCode(TypedDict):
    code: str
    expires_in: int


class LoginCodeCooldown(Exception):
    """Backend juda tez-tez so'ralganini bildiradi (429)."""


def generate_login_code(
    telegram_user_id: int,
    telegram_username: str = "",
    telegram_first_name: str = "",
) -> Optional[LoginCode]:
    """
    Foydalanuvchi botga /start yuborganda (yoki yangi kod so'raganda) chaqiriladi.
    Django backend yangi bir martalik login kodi yaratadi.

    Returns:
        {"code": "123456", "expires_in": 60}  — muvaffaqiyatli bo'lsa
        None                                   — kutilmagan xato yuz bersa

    Raises:
        LoginCodeCooldown — juda tez-tez so'ralsa (429)
    """
    url = f"{BASE}/api/v1/auth/telegram/generate-code/"
    payload = {
        "telegram_user_id": telegram_user_id,
        "telegram_username": telegram_username,
        "telegram_first_name": telegram_first_name,
    }
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            logger.info("Login code generated: telegram_user_id=%s", telegram_user_id)
            return {"code": data["code"], "expires_in": data["expires_in"]}
        if resp.status_code == 429:
            raise LoginCodeCooldown()
        logger.warning(
            "generate_login_code failed: status=%s body=%s", resp.status_code, resp.text[:200]
        )
        return None
    except requests.RequestException as exc:
        logger.exception("generate_login_code network error: %s", exc)
        return None
