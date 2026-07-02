from django.urls import path
from apps.couriers.api.views import (
    CourierProfileView,
    CourierGoOnlineView,
    CourierGoOfflineView,
    CourierLocationPingView,
    CourierActiveOrdersView,
    CourierEarningsView,
    CourierShiftView,
)

urlpatterns = [
    path("courier/profile/", CourierProfileView.as_view(), name="courier-profile"),
    path("courier/go-online/", CourierGoOnlineView.as_view(), name="courier-go-online"),
    path("courier/go-offline/", CourierGoOfflineView.as_view(), name="courier-go-offline"),
    path("courier/location-ping/", CourierLocationPingView.as_view(), name="courier-location-ping"),
    path("courier/orders/", CourierActiveOrdersView.as_view(), name="courier-orders"),
    path("courier/earnings/", CourierEarningsView.as_view(), name="courier-earnings"),
    path("courier/shift/", CourierShiftView.as_view(), name="courier-shift"),
]
