from django.urls import path
from apps.carts.api.views import (
    CartView,
    CartAddItemView,
    CartItemUpdateView,
    CartItemDeleteView,
    CartApplyPromoView,
    CartClearView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart-detail"),
    path("cart/items/", CartAddItemView.as_view(), name="cart-add-item"),
    path("cart/items/<uuid:pk>/", CartItemUpdateView.as_view(), name="cart-item-update"),
    path("cart/items/<uuid:pk>/delete/", CartItemDeleteView.as_view(), name="cart-item-delete"),
    path("cart/apply-promo/", CartApplyPromoView.as_view(), name="cart-apply-promo"),
    path("cart/clear/", CartClearView.as_view(), name="cart-clear"),
]
