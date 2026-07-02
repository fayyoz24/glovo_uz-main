from django.apps import AppConfig


class PromotionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.promotions"
    verbose_name = "Promotions"

    def ready(self):
        # Signal'larni ro'yxatdan o'tkazish (agar kerak bo'lsa)
        pass  # noqa: promotions.signals import qilish shu yerda
