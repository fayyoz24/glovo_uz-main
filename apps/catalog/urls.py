from django.urls import path
from apps.catalog.api.views import (
    CategoryListView,
    BranchProductListView,
    ProductDetailView,
    ProductSearchView,
    MerchantProductListView,
    MerchantProductCreateView,
    MerchantProductUpdateView,
    ProductToggleAvailabilityView,
)

urlpatterns = [
    # Public
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("merchants/<uuid:merchant_pk>/products/", BranchProductListView.as_view(), name="branch-products"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("search/", ProductSearchView.as_view(), name="product-search"),

    # Merchant panel
    path("merchant/products/", MerchantProductListView.as_view(), name="merchant-product-list"),
    path("merchant/products/create/", MerchantProductCreateView.as_view(), name="merchant-product-create"),
    path("merchant/products/<uuid:pk>/", MerchantProductUpdateView.as_view(), name="merchant-product-update"),
    path("merchant/products/<uuid:pk>/toggle-availability/", ProductToggleAvailabilityView.as_view(), name="merchant-product-toggle"),
]