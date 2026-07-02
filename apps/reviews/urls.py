"""
Reviews customer & public URL configuration.

config/urls.py ga:
    path("api/v1/", include("reviews.urls")),
    path("api/v1/admin/", include("reviews.admin_urls")),
"""
from django.urls import path

from apps.reviews.api.views import (
    MerchantRatingStatsView,
    MerchantReviewListView,
    MyReviewsView,
    OrderReviewCreateView,
    ReviewDetailUpdateView,
    ReviewFlagView,
)

urlpatterns = [
    # Buyurtma uchun review yozish
    path(
        "orders/<uuid:order_id>/review/",
        OrderReviewCreateView.as_view(),
        name="order-review-create",
    ),
    # Mijozning o'z reviewlari
    path("reviews/my/", MyReviewsView.as_view(), name="my-reviews"),
    # Review detail / tahrirlash
    path(
        "reviews/<uuid:review_id>/",
        ReviewDetailUpdateView.as_view(),
        name="review-detail-update",
    ),
    # Shikoyat
    path(
        "reviews/<uuid:review_id>/flag/",
        ReviewFlagView.as_view(),
        name="review-flag",
    ),
    # Public – do'kon reviewlari
    path(
        "merchants/<uuid:merchant_id>/reviews/",
        MerchantReviewListView.as_view(),
        name="merchant-reviews",
    ),
    path(
        "merchants/<uuid:merchant_id>/rating-stats/",
        MerchantRatingStatsView.as_view(),
        name="merchant-rating-stats",
    ),
]
