"""
telegram_bot/main.py

Bot ishga tushirish — ikkita rejim:

  POLLING (local dev):
      python -m telegram_bot.main

  WEBHOOK (production):
      python -m telegram_bot.main --webhook
      Keyin Telegram'ga webhook URL ni register qiladi va kutadi.

Muhit o'zgaruvchilari (.env):
    TELEGRAM_BOT_TOKEN        — bot tokeni
    TELEGRAM_BOT_SHARED_SECRET — bot <-> Django o'rtasidagi umumiy maxfiy kalit
    TELEGRAM_WEBHOOK_URL      — https://api.yourdomain.uz/bot/webhook/  (bot o'z Telegram webhook'i uchun)
    BACKEND_BASE_URL          — http://localhost:8000  (yoki prod URL)
"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from telegram_bot.config import BOT_TOKEN
from telegram_bot.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    mode = sys.argv[1] if len(sys.argv) > 1 else "polling"

    if mode == "--webhook":
        await _run_webhook(bot, dp)
    else:
        await _run_polling(bot, dp)


async def _run_polling(bot: Bot, dp: Dispatcher) -> None:
    """Local dev uchun polling rejimi."""
    logger.info("Bot polling rejimida ishga tushdi...")
    # Eski webhook ni o'chirib, polling boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def _run_webhook(bot: Bot, dp: Dispatcher) -> None:
    """
    Production uchun webhook rejimi.

    Eslatma: production da odatda Django'ning
    /api/v1/auth/telegram/webhook/ endpointi bot xabarlarini qabul qiladi
    va confirm_telegram_link() ni chaqiradi.

    Agar alohida bot serveri kerak bo'lsa, bu rejim ishga tushiriladi.
    """
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    from aiohttp import web
    from telegram_bot.config import BOT_SHARED_SECRET, WEBHOOK_URL

    if not WEBHOOK_URL:
        logger.error("TELEGRAM_WEBHOOK_URL sozlanmagan! .env faylini tekshiring.")
        return

    # Telegram'ga webhook URL ni register qilish
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=BOT_SHARED_SECRET,
        drop_pending_updates=True,
    )
    logger.info("Webhook registered: %s", WEBHOOK_URL)

    # aiohttp server (port 8080)
    app = web.Application()
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=BOT_SHARED_SECRET,
    )
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()
    logger.info("Webhook server 0.0.0.0:8080 da ishlamoqda...")

    # To'xtatilguncha kutish
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
