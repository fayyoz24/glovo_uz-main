from django.urls import path

from apps.carts.api.views import (
    CartView,
    CartItemAddView,
    CartItemUpdateView,
    CartItemDeleteView,
    CartApplyPromoView,
    CartClearView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),

    path("cart/items/", CartItemAddView.as_view(), name="cart-item-add"),

    path(
        "cart/items/<uuid:pk>/",
        CartItemUpdateView.as_view(),
        name="cart-item-update",
    ),

    path(
        "cart/items/<uuid:pk>/delete/",
        CartItemDeleteView.as_view(),
        name="cart-item-delete",
    ),

    path(
        "cart/apply-promo/",
        CartApplyPromoView.as_view(),
        name="cart-apply-promo",
    ),

    path(
        "cart/clear/",
        CartClearView.as_view(),
        name="cart-clear",
    ),
]