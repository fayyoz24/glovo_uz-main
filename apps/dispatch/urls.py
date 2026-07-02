from django.urls import path
from apps.dispatch.api.views import (
    CourierAvailableOrdersView,
    CourierAcceptOrderView,
    CourierRejectOrderView,
    CourierPickedUpView,
    CourierDeliveredView,
    CourierAssignmentHistoryView,
)

urlpatterns = [
    path("courier/orders/available/", CourierAvailableOrdersView.as_view(), name="courier-available-orders"),
    path("courier/orders/<uuid:assignment_id>/accept/", CourierAcceptOrderView.as_view(), name="courier-accept"),
    path("courier/orders/<uuid:assignment_id>/reject/", CourierRejectOrderView.as_view(), name="courier-reject"),
    path("courier/orders/<uuid:order_id>/picked-up/", CourierPickedUpView.as_view(), name="courier-picked-up"),
    path("courier/orders/<uuid:order_id>/delivered/", CourierDeliveredView.as_view(), name="courier-delivered"),
    path("courier/assignments/", CourierAssignmentHistoryView.as_view(), name="courier-assignment-history"),
]
