from rest_framework import serializers
from apps.locations.models import Address, ServiceZone


# apps/locations/api/serializers.py

DEFAULT_CITY = "Qarshi"



class AddressSerializer(serializers.ModelSerializer):
    city = serializers.CharField(read_only=True)  # har doim model default'idan keladi, o'zgartirib bo'lmaydi

    # Brauzer Geolocation API'si odatda 6 tadan ko'p o'nlik xonali son
    # qaytaradi (masalan 41.31108123456789). ModelSerializer avtomatik
    # generatsiya qiladigan qat'iy DecimalField(max_digits=9, decimal_places=6)
    # bunday qiymatlarni "Ensure that there are no more than 9 digits in
    # total" xatosi bilan rad etardi. FloatField bunga yo'l qo'ymaydi;
    # DB saqlashda model maydoni baribir mos aniqlikka yaxlitlaydi.
    latitude = serializers.FloatField(required=False, allow_null=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=False, allow_null=True, min_value=-180, max_value=180)

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
