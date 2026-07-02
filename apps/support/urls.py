from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.support.api.views import (
    AdminComplaintViewSet,
    CustomerComplaintViewSet,
    DisputeViewSet,
    RefundRequestViewSet,
)

# ---- Customer-facing router ------------------------------------------------
customer_router = DefaultRouter()
customer_router.register(
    r"complaints",
    CustomerComplaintViewSet,
    basename="customer-complaint",
)
customer_router.register(
    r"disputes",
    DisputeViewSet,
    basename="dispute",
)
customer_router.register(
    r"refunds",
    RefundRequestViewSet,
    basename="refund-request",
)

# ---- Admin / support-agent router ------------------------------------------
admin_router = DefaultRouter()
admin_router.register(
    r"support/complaints",
    AdminComplaintViewSet,
    basename="admin-complaint",
)

# Admin reuses the same DisputeViewSet and RefundRequestViewSet
# (permission checks are done inside the views)
admin_router.register(
    r"support/disputes",
    DisputeViewSet,
    basename="admin-dispute",
)
admin_router.register(
    r"support/refunds",
    RefundRequestViewSet,
    basename="admin-refund",
)

# ---- URL patterns exported for config/urls.py ------------------------------
# In config/urls.py, include like:
#   path("api/v1/support/", include("support.api.urls", namespace="support")),
# But since admin_router paths already have "support/" prefix, mount admin_router at:
#   path("api/v1/admin/", include(admin_router.urls)),

app_name = "support"

urlpatterns = [
    path("", include(customer_router.urls)),
]

# Separate export for admin urls (mounted under /api/v1/admin/ in config/urls.py)
admin_urlpatterns = admin_router.urls
