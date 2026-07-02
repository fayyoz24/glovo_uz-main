"""
telegram_bot/handlers.py

Barcha bot handler'lari shu yerda.

Foydalanuvchi oqimi (42.uz uslubida — yagona auth usuli):
  1. Foydalanuvchi saytda "Kodni kiriting" oynasini ko'radi:
        "@GlovoUZBot botiga kiring va 1 daqiqalik kodingizni oling."
  2. Foydalanuvchi botga o'tadi va /start yuboradi (yoki "🔄 Yangi kod" tugmasini bosadi).
  3. Bot Django backend'dan yangi bir martalik kod so'raydi va uni foydalanuvchiga yuboradi.
  4. Foydalanuvchi shu kodni saytga kiritadi — sayt backend orqali kodni tasdiqlaydi
     va foydalanuvchini tizimga kiritadi (kerak bo'lsa akkaunt avtomatik yaratiladi).

Boshqa hech qanday login usuli (telefon/SMS/parol) mavjud emas.
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from telegram_bot.django_client import generate_login_code, LoginCodeCooldown

logger = logging.getLogger(__name__)
router = Router()

NEW_CODE_BUTTON_TEXT = "🔄 Yangi kod olish"

KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=NEW_CODE_BUTTON_TEXT)]],
    resize_keyboard=True,
)


async def _send_login_code(message: Message) -> None:
    """Yangi login kodi yaratib, foydalanuvchiga yuboradi."""
    user = message.from_user

    try:
        result = generate_login_code(
            telegram_user_id=user.id,
            telegram_username=user.username or "",
            telegram_first_name=user.first_name or "",
        )
    except LoginCodeCooldown:
        await message.answer(
            "⏳ Juda tez-tez so'ramoqdasiz.\n"
            "Iltimos, bir necha soniyadan so'ng qaytadan urinib ko'ring.",
            reply_markup=KEYBOARD,
        )
        return

    if result is None:
        await message.answer(
            "❌ Kod yaratishda xatolik yuz berdi.\n"
            "Birozdan so'ng qaytadan urinib ko'ring yoki /help buyrug'ini yuboring.",
            reply_markup=KEYBOARD,
        )
        return

    code = result["code"]
    expires_in = result["expires_in"]

    await message.answer(
        f"🔑 Sizning kodingiz:\n\n"
        f"<code>{code}</code>\n\n"
        f"⏱ Kod {expires_in} soniya amal qiladi.\n"
        f"Ushbu kodni Glovo UZ saytidagi \"Kodni kiriting\" oynasiga kiriting.",
        reply_markup=KEYBOARD,
    )
    logger.info("Login code sent: user_id=%s username=%s", user.id, user.username)


# ─────────────────────────────────────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>Glovo UZ</b> botiga xush kelibsiz!\n\n"
        "Saytga kirish uchun quyidagi bir martalik kodingizdan foydalaning 👇",
        reply_markup=KEYBOARD,
    )
    await _send_login_code(message)


# ─────────────────────────────────────────────────────────────────────────────
#  "🔄 Yangi kod olish" tugmasi / /code buyrug'i
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("code"))
@router.message(lambda message: message.text == NEW_CODE_BUTTON_TEXT)
async def cmd_new_code(message: Message) -> None:
    await _send_login_code(message)


# ─────────────────────────────────────────────────────────────────────────────
#  /help
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "Glovo UZ saytiga kirish uchun:\n"
        "1. Saytda \"Kodni kiriting\" oynasini oching\n"
        "2. Shu botga /start yuboring (yoki 🔄 Yangi kod olish tugmasini bosing)\n"
        "3. Botdan kelgan kodni saytga kiriting\n\n"
        "Kod atigi 1 daqiqa amal qiladi — muddati o'tsa, yangisini so'rang.\n\n"
        "Muammo bo'lsa: <a href='https://glovo.uz/support'>Qo'llab-quvvatlash</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=KEYBOARD,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Boshqa xabarlar
# ─────────────────────────────────────────────────────────────────────────────

@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Bu bot faqat Glovo UZ saytiga kirish uchun bir martalik kod beradi.\n"
        "Yangi kod olish uchun /start yuboring yoki quyidagi tugmani bosing.",
        reply_markup=KEYBOARD,
    )
