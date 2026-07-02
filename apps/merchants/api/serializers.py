from rest_framework import serializers
from apps.merchants.models import Merchant, MerchantBranch, BranchWorkingHour


class BranchWorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchWorkingHour
        fields = ["id", "weekday", "open_time", "close_time", "is_closed"]
        read_only_fields = ["id"]


class MerchantBranchSerializer(serializers.ModelSerializer):
    working_hours = BranchWorkingHourSerializer(many=True, read_only=True)

    class Meta:
        model = MerchantBranch
        fields = [
            "id", "name", "phone", "address_text",
            "latitude", "longitude", "service_radius_km",
            "prep_time_min", "is_open", "accepting_orders",
            "working_hours", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MerchantListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    class Meta:
        model = Merchant
        fields = ["id", "name", "slug", "type", "logo", "rating_avg", "total_reviews", "status"]
        read_only_fields = ["id", "slug", "rating_avg", "total_reviews"]


class MerchantDetailSerializer(serializers.ModelSerializer):
    branches = MerchantBranchSerializer(many=True, read_only=True)

    class Meta:
        model = Merchant
        fields = [
            "id", "name", "slug", "type", "description",
            "logo", "cover", "rating_avg", "total_reviews",
            "status", "branches", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "rating_avg", "total_reviews", "status", "created_at", "updated_at"]


class MerchantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ["name", "type", "description", "logo", "cover"]
