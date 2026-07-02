from rest_framework import serializers
from apps.locations.models import Address, ServiceZone


# apps/locations/api/serializers.py

DEFAULT_CITY = "Qarshi"



class AddressSerializer(serializers.ModelSerializer):
    city = serializers.CharField(read_only=True)  # har doim model default'idan keladi, o'zgartirib bo'lmaydi

    class Meta:
        model = Address
        fields = [
            "id", "title", "address_line", "landmark",
            "entrance", "floor", "apartment",
            "latitude", "longitude", "district", "city",
            "is_default", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ServiceZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceZone
        fields = ["id", "name", "city", "center_lat", "center_lng", "radius_km", "is_active"]
        read_only_fields = ["id"]
