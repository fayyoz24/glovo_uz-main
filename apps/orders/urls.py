from django.urls import path
from apps.orders.api.views import (
    CheckoutView,
    CustomerOrderListView,
    CustomerOrderDetailView,
    CustomerOrderCancelView,
    OrderTrackView,
    MerchantOrderListView,
    MerchantConfirmOrderView,
    MerchantRejectOrderView,
    MerchantPreparingOrderView,
    MerchantReadyOrderView,
)

urlpatterns = [
    # Customer
    path("orders/checkout/", CheckoutView.as_view(), name="order-checkout"),
    path("orders/", CustomerOrderListView.as_view(), name="order-list"),
    path("orders/<uuid:pk>/", CustomerOrderDetailView.as_view(), name="order-detail"),
    path("orders/<uuid:pk>/cancel/", CustomerOrderCancelView.as_view(), name="order-cancel"),
    path("orders/<uuid:pk>/track/", OrderTrackView.as_view(), name="order-track"),

    # Merchant Panel
    path("merchant/orders/", MerchantOrderListView.as_view(), name="merchant-order-list"),
    path("merchant/orders/<uuid:pk>/confirm/", MerchantConfirmOrderView.as_view(), name="merchant-order-confirm"),
    path("merchant/orders/<uuid:pk>/reject/", MerchantRejectOrderView.as_view(), name="merchant-order-reject"),
    path("merchant/orders/<uuid:pk>/preparing/", MerchantPreparingOrderView.as_view(), name="merchant-order-preparing"),
    path("merchant/orders/<uuid:pk>/ready/", MerchantReadyOrderView.as_view(), name="merchant-order-ready"),
]
