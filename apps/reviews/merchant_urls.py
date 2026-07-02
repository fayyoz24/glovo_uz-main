from django.urls import path

from reviews.api.views import MerchantPanelReviewListView, MerchantReplyView

urlpatterns = [
    path("reviews/", MerchantPanelReviewListView.as_view(), name="merchant-panel-reviews"),
    path(
        "reviews/<uuid:review_id>/reply/",
        MerchantReplyView.as_view(),
        name="merchant-review-reply",
    ),
]
