"""
Django settings for dasturxon project.
"""
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-change-me-in-production")

DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")


# ─── Applications ────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "daphne",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "apps.accounts",
    "apps.analytics",
    "apps.common",
    "apps.locations",
    "apps.merchants",
    "apps.catalog",
    "apps.carts",
    "apps.orders",
    "apps.couriers",
    "apps.dispatch",
    "apps.payments",
    "apps.promotions",
    "apps.notifications",
    "apps.reviews",
    "apps.support",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "django_celery_beat",
    "channels",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
AUTH_USER_MODEL = "accounts.User"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ─── Database ────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ─── Auth ────────────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MIN", default=15, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=30, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# ─── Internationalization ────────────────────────────────────────────────────

LANGUAGE_CODE = "uz"          # FIX: RU emas, UZ
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True


# ─── Static ──────────────────────────────────────────────────────────────────

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Catalog ─────────────────────────────────────────────────────────────────
# Mahsulot rasmi uchun maksimal hajm (KB). Do'kon egasi shundan katta rasm yuklay olmaydi.
PRODUCT_IMAGE_MAX_SIZE_KB = config("PRODUCT_IMAGE_MAX_SIZE_KB", default=200, cast=int)


# ─── Channels (WebSocket) ────────────────────────────────────────────────────

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(
                config("REDIS_HOST", default="127.0.0.1"),
                config("REDIS_PORT", default=6379, cast=int),
            )],
        },
    }
}


# ─── Celery ──────────────────────────────────────────────────────────────────

from celery.schedules import crontab

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_TIMEZONE = "Asia/Tashkent"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)

CELERY_BEAT_SCHEDULE = {
    "sweep-expired-offers": {
        "task": "apps.dispatch.tasks.sweep_expired_offers",
        "schedule": 60.0,
    },
    "auto-cancel-unpaid-orders": {
        "task": "apps.orders.tasks.auto_cancel_unpaid_orders",
        "schedule": crontab(minute="*/5"),
    },
    "cleanup-stale-carts": {
        "task": "apps.orders.tasks.cleanup_stale_carts",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "cleanup-old-location-pings": {
        "task": "apps.couriers.tasks.cleanup_old_location_pings",
        "schedule": crontab(minute=0, hour=2),
    },
    "auto-end-stale-shifts": {
        "task": "apps.couriers.tasks.auto_end_stale_shifts",
        "schedule": crontab(minute=0),
    },
    "retry-failed-notifications": {
        "task": "notifications.retry_failed_notifications",
        "schedule": crontab(minute="*/10"),
    },
    "cleanup-old-notifications": {
        "task": "notifications.cleanup_old_notifications",
        "schedule": crontab(minute=0, hour=3),
    },
    "daily-analytics-snapshot": {
        "task": "apps.analytics.tasks.daily_aggregation.run_daily_aggregation",
        "schedule": crontab(minute=0, hour=1),
    },
    "expire-stale-promos": {
        "task": "apps.promotions.tasks.expire_stale_promos",
        "schedule": crontab(minute=0, hour=0),
    },
    "auto-activate-scheduled-promos": {
        "task": "apps.promotions.tasks.auto_activate_scheduled_promos",
        "schedule": crontab(minute="*/5"),
    },
}


# ─── FCM (Firebase Cloud Messaging) ─────────────────────────────────────────

FCM_SERVER_KEY = config("FCM_SERVER_KEY", default="")


# ─── SMS ─────────────────────────────────────────────────────────────────────

SMS_PROVIDER = config("SMS_PROVIDER", default="eskiz")
ESKIZ_EMAIL = config("ESKIZ_EMAIL", default="")
ESKIZ_PASSWORD = config("ESKIZ_PASSWORD", default="")
ESKIZ_FROM = "4546"

PLAYMOBILE_USERNAME = config("PLAYMOBILE_USERNAME", default="")
PLAYMOBILE_PASSWORD = config("PLAYMOBILE_PASSWORD", default="")
PLAYMOBILE_ORIGINATOR = config("PLAYMOBILE_ORIGINATOR", default="Dasturxon")


# ─── Telegram Bot ────────────────────────────────────────────────────────────
# FIX: duplikat o'chirildi, barcha Telegram o'zgaruvchilari bir joyda

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_BOT_USERNAME = config("TELEGRAM_BOT_USERNAME", default="")      # @ belgisisiz
# Bot <-> Backend o'rtasidagi ichki so'rovlarni himoya qiluvchi umumiy maxfiy kalit
# (bot shu qiymatni X-Telegram-Bot-Api-Secret-Token header'ida yuboradi).
TELEGRAM_BOT_SHARED_SECRET = config("TELEGRAM_BOT_SHARED_SECRET", default="")
TELEGRAM_ADMIN_CHAT_ID = config("TELEGRAM_ADMIN_CHAT_ID", default="")


# ─── Email ───────────────────────────────────────────────────────────────────

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@dasturxon.uz")


# ─── Telegram login code ─────────────────────────────────────────────────────
# Bot orqali yuboriladigan bir martalik kodlar bilan bog'liq sozlamalar
# apps/accounts/constants.py da: LOGIN_CODE_LENGTH, LOGIN_CODE_EXPIRY_SECONDS va h.k.


# ─── CORS ────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5173",
).split(",")


# ─── Sentry ──────────────────────────────────────────────────────────────────
# FIX: Sentry endi to'g'ri initialize qilinadi

SENTRY_DSN = config("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
    )
