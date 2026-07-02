from rest_framework import serializers
from apps.locations.models import Address, ServiceZone


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "title", "address_line", "landmark",
            "entrance", "floor", "apartment",
            "latitude", "longitude",
            "district", "city", "is_default",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ServiceZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceZone
        fields = ["id", "name", "city", "center_lat", "center_lng", "radius_km", "is_active"]
        read_only_fields = ["id"]
