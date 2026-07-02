from django.contrib import admin
from apps.locations.models import Address, ServiceZone, GeocodingCache


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "address_line", "city", "is_default"]
    list_filter = ["city", "is_default"]
    search_fields = ["user__phone", "address_line", "landmark"]


@admin.register(ServiceZone)
class ServiceZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "radius_km", "is_active"]
    list_filter = ["city", "is_active"]


@admin.register(GeocodingCache)
class GeocodingCacheAdmin(admin.ModelAdmin):
    list_display = ["query", "latitude", "longitude", "provider", "created_at"]
    search_fields = ["query"]
