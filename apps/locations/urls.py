from django.urls import path
from apps.locations.api.views import (
    AddressListCreateView,
    AddressDetailView,
    SetDefaultAddressView,
    ServiceZoneListView,
)

urlpatterns = [
    path("addresses/", AddressListCreateView.as_view(), name="address-list"),
    path("addresses/<uuid:pk>/", AddressDetailView.as_view(), name="address-detail"),
    path("addresses/<uuid:pk>/set-default/", SetDefaultAddressView.as_view(), name="address-set-default"),
    path("zones/", ServiceZoneListView.as_view(), name="zone-list"),
]
