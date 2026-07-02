from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/v1/", include([
        path("", include("apps.accounts.urls")),
        path("", include("apps.locations.urls")),
        path("", include("apps.merchants.urls")),
        path("", include("apps.analytics.urls")),
        path("", include("apps.carts.urls")),
        path("", include("apps.catalog.urls")),
        path("", include("apps.common.urls")),
        path("", include("apps.couriers.urls")),
        path("", include("apps.dispatch.urls")),
        path("", include("apps.notifications.urls")),
        path("", include("apps.orders.urls")),
        path("", include("apps.payments.urls")),
        path("", include("apps.promotions.urls")),
        path("", include("apps.reviews.urls")),
        path("", include("apps.support.urls")),
    ])),
]
