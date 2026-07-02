from django.urls import path

from reviews.api.views import (
    AdminReviewDetailView,
    AdminReviewHideView,
    AdminReviewListView,
    AdminReviewRestoreView,
)

urlpatterns = [
    path("reviews/", AdminReviewListView.as_view(), name="admin-review-list"),
    path("reviews/<uuid:review_id>/", AdminReviewDetailView.as_view(), name="admin-review-detail"),
    path("reviews/<uuid:review_id>/hide/", AdminReviewHideView.as_view(), name="admin-review-hide"),
    path(
        "reviews/<uuid:review_id>/restore/",
        AdminReviewRestoreView.as_view(),
        name="admin-review-restore",
    ),
]
