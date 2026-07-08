from django.urls import path
from apps.merchants.api.views import (
    MerchantListView,
    MerchantDetailView,
    MerchantCreateView,
    NearbyMerchantsView,
    MerchantBranchListView,
    BranchToggleOrdersView,
    MerchantStaffProfileView,
    MerchantStaffToggleAcceptingOrdersView,
)

urlpatterns = [
    path("merchants/", MerchantListView.as_view(), name="merchant-list"),
    path("merchants/nearby/", NearbyMerchantsView.as_view(), name="merchant-nearby"),
    path("merchants/create/", MerchantCreateView.as_view(), name="merchant-create"),
    path("merchants/<uuid:pk>/", MerchantDetailView.as_view(), name="merchant-detail"),
    path("merchants/<uuid:merchant_pk>/branches/", MerchantBranchListView.as_view(), name="branch-list"),
    path(
        "merchants/<uuid:merchant_pk>/branches/<uuid:branch_pk>/toggle-orders/",
        BranchToggleOrdersView.as_view(),
        name="branch-toggle-orders",
    ),

    # Merchant Panel — joriy tizimga kirgan merchant xodimi uchun
    path("merchant/profile/", MerchantStaffProfileView.as_view(), name="merchant-staff-profile"),
    path(
        "merchant/branch/toggle-orders/",
        MerchantStaffToggleAcceptingOrdersView.as_view(),
        name="merchant-staff-toggle-orders",
    ),
]
