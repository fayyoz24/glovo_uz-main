from django.urls import path
from apps.merchants.api.views import (
    MerchantListView,
    MerchantDetailView,
    MerchantCreateView,
    NearbyMerchantsView,
    MerchantBranchListView,
    BranchToggleOrdersView,
    MerchantSelfRegisterView,
    MyMerchantApplicationsView,
    MyMerchantView,
    MyBranchView,
    MyBranchesView,
    MyBranchDetailView,
    MyBranchSwitchView,
    MerchantStaffProfileView,
    MerchantStaffToggleAcceptingOrdersView,
    AdminPendingMerchantsView,
    AdminMerchantApproveView,
    AdminMerchantRejectView,
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
    path("merchant/register/", MerchantSelfRegisterView.as_view(), name="merchant-self-register"),
    path("merchant/applications/", MyMerchantApplicationsView.as_view(), name="merchant-applications"),
    path("merchant/mine/", MyMerchantView.as_view(), name="merchant-mine"),
    path("merchant/branch/", MyBranchView.as_view(), name="merchant-my-branch"),
    path("merchant/branches/", MyBranchesView.as_view(), name="merchant-my-branches"),
    path("merchant/branches/<uuid:branch_pk>/", MyBranchDetailView.as_view(), name="merchant-my-branch-detail"),
    path("merchant/branches/<uuid:branch_pk>/switch/", MyBranchSwitchView.as_view(), name="merchant-my-branch-switch"),
    path("merchant/profile/", MerchantStaffProfileView.as_view(), name="merchant-staff-profile"),
    path(
        "merchant/branch/toggle-orders/",
        MerchantStaffToggleAcceptingOrdersView.as_view(),
        name="merchant-staff-toggle-orders",
    ),

    # Admin panel — do'konlarni tasdiqlash / rad etish
    path("admin/merchants/pending/", AdminPendingMerchantsView.as_view(), name="admin-merchants-pending"),
    path("admin/merchants/<uuid:pk>/approve/", AdminMerchantApproveView.as_view(), name="admin-merchant-approve"),
    path("admin/merchants/<uuid:pk>/reject/", AdminMerchantRejectView.as_view(), name="admin-merchant-reject"),
]
