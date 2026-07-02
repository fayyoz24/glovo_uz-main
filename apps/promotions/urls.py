"""
Promotions URL configuration.

config/urls.py da quyidagicha ulanadi:

    # Customer
    path("api/v1/promotions/", include("promotions.urls")),

    # Admin
    path("api/v1/admin/promotions/", include("promotions.admin_urls")),
"""
from django.urls import path

from apps.promotions.api.views import (
    MyReferralCodeView,
    PromoValidateView,
)

urlpatterns = [
    # Promo kodni tekshirish (cart'da apply qilishdan avval)
    path("validate/", PromoValidateView.as_view(), name="promo-validate"),
    # O'z referal kodini ko'rish / yaratish
    path("referral/", MyReferralCodeView.as_view(), name="my-referral-code"),
]
