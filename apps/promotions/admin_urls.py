from django.urls import path

from promotions.api.views import (
    AdminPromoActivateView,
    AdminPromoCampaignDetailView,
    AdminPromoCampaignListCreateView,
    AdminPromoPauseView,
    AdminPromoUsagesView,
)

urlpatterns = [
    path("", AdminPromoCampaignListCreateView.as_view(), name="admin-promo-list-create"),
    path("<uuid:promo_id>/", AdminPromoCampaignDetailView.as_view(), name="admin-promo-detail"),
    path("<uuid:promo_id>/pause/", AdminPromoPauseView.as_view(), name="admin-promo-pause"),
    path("<uuid:promo_id>/activate/", AdminPromoActivateView.as_view(), name="admin-promo-activate"),
    path("<uuid:promo_id>/usages/", AdminPromoUsagesView.as_view(), name="admin-promo-usages"),
]
