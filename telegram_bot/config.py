"""
telegram_bot/config.py

Bot uchun konfiguratsiya — .env dan o'qiladi.
"""
from decouple import config

BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN")

# Bot <-> Django backend o'rtasidagi so'rovlarni himoya qiluvchi umumiy maxfiy kalit.
# Django tarafida bir xil qiymat settings.TELEGRAM_BOT_SHARED_SECRET da turishi kerak.
BOT_SHARED_SECRET: str = config("TELEGRAM_BOT_SHARED_SECRET")

# Django backend base URL (login kodi so'rash uchun)
BACKEND_BASE_URL: str = config("BACKEND_BASE_URL", default="http://localhost:8000")

# Bot o'z webhook URL si (Telegram serverlariga o'z yangilanishlarini yuborish uchun
# ro'yxatdan o'tkaziladigan manzil — Django webhook bilan aloqasi yo'q).
# Masalan: https://api.yourdomain.uz/bot/webhook/
WEBHOOK_URL: str = config("TELEGRAM_WEBHOOK_URL", default="")
