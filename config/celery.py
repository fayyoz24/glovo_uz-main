import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("glovo_uz")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {

    # ── accounts ──────────────────────────────────────────────────────────────
    "clean-expired-login-codes": {
        "task": "apps.accounts.tasks.clean_expired_login_codes",
        "schedule": crontab(minute=0, hour=3),        # har kecha 03:00
        "options": {"queue": "maintenance"},
    },

    # ── carts ─────────────────────────────────────────────────────────────────
    "expire-old-carts": {
        "task": "apps.carts.tasks.expire_old_carts",
        "schedule": crontab(minute=0, hour="*/6"),     # har 6 soatda
        "options": {"queue": "maintenance"},
    },
    "notify-abandoned-carts": {
        "task": "apps.carts.tasks.notify_abandoned_carts",
        "schedule": crontab(minute=0, hour=10),        # har kuni 10:00
        "options": {"queue": "notifications"},
    },

    # ── catalog ───────────────────────────────────────────────────────────────
    "sync-product-availability": {
        "task": "apps.catalog.tasks.sync_product_availability",
        "schedule": crontab(minute="*/15"),            # har 15 daqiqada
        "options": {"queue": "catalog"},
    },

    # ── merchants ─────────────────────────────────────────────────────────────
    "auto-open-close-branches": {
        "task": "apps.merchants.tasks.auto_open_close_branches",
        "schedule": crontab(minute="*/5"),             # har 5 daqiqada
        "options": {"queue": "merchants"},
    },
    "send-daily-merchant-report": {
        "task": "apps.merchants.tasks.send_daily_merchant_report",
        "schedule": crontab(minute=0, hour=8),         # har kuni 08:00
        "options": {"queue": "notifications"},
    },

    # ── locations ─────────────────────────────────────────────────────────────
    "clean-geocoding-cache": {
        "task": "apps.locations.tasks.clean_old_geocoding_cache",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),  # har dushanba 02:00
        "options": {"queue": "maintenance"},
    },

    # ── notifications ────────────────────────────────────────────────────────────────
    "retry-failed-notifications": {
        "task": "notifications.retry_failed_notifications",
        "schedule": crontab(minute="*/10"),
    },
    "cleanup-old-notifications": {
        "task": "notifications.cleanup_old_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
}

app.conf.task_queues_default_exchange = "default"
app.conf.task_default_queue = "default"
app.conf.task_queues = {
    "default": {"exchange": "default"},
    "maintenance": {"exchange": "maintenance"},
    "notifications": {"exchange": "notifications"},
    "catalog": {"exchange": "catalog"},
    "merchants": {"exchange": "merchants"},
}
