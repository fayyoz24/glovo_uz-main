from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.api.views import (
    TelegramGenerateCodeView,
    TelegramVerifyCodeView,
    MeView,
)

urlpatterns = [
    # Telegram-only auth
    path("auth/telegram/generate-code/", TelegramGenerateCodeView.as_view(), name="telegram-generate-code"),
    path("auth/telegram/verify-code/",   TelegramVerifyCodeView.as_view(),   name="telegram-verify-code"),

    # JWT
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Profile
    path("auth/me/", MeView.as_view(), name="me"),
]
