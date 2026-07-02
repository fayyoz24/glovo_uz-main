from django.urls import path
from apps.analytics.api.views.dashboard import (
    AdminDashboardFullAPIView,
    AdminDashboardOverviewAPIView,
    AdminDashboardOrdersAPIView,
    AdminDashboardRevenueAPIView,
    AdminDashboardMerchantsAPIView,
    AdminDashboardCouriersAPIView,
)

app_name = "analytics"

urlpatterns = [
    path("admin/dashboard/", AdminDashboardFullAPIView.as_view(), name="admin-dashboard-full"),
    path("admin/dashboard/overview/", AdminDashboardOverviewAPIView.as_view(), name="admin-dashboard-overview"),
    path("admin/dashboard/orders/", AdminDashboardOrdersAPIView.as_view(), name="admin-dashboard-orders"),
    path("admin/dashboard/revenue/", AdminDashboardRevenueAPIView.as_view(), name="admin-dashboard-revenue"),
    path("admin/dashboard/merchants/", AdminDashboardMerchantsAPIView.as_view(), name="admin-dashboard-merchants"),
    path("admin/dashboard/couriers/", AdminDashboardCouriersAPIView.as_view(), name="admin-dashboard-couriers"),
]
