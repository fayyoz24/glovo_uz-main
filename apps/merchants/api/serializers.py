from rest_framework import serializers
from apps.merchants.models import Merchant, MerchantBranch, BranchWorkingHour
from apps.common.utils.fields import CompressedImageField


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
        fields = ["id", "name", "slug", "type", "logo", "cover", "rating_avg", "total_reviews", "status"]
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
    logo = CompressedImageField(required=False, allow_null=True)
    cover = CompressedImageField(required=False, allow_null=True)

    class Meta:
        model = Merchant
        fields = ["name", "type", "description", "logo", "cover"]


class MerchantUpdateSerializer(serializers.ModelSerializer):
    logo = CompressedImageField(required=False, allow_null=True)
    cover = CompressedImageField(required=False, allow_null=True)

    class Meta:
        model = Merchant
        fields = ["name", "type", "description", "logo", "cover"]
        extra_kwargs = {field: {"required": False} for field in fields}


class MerchantStaffProfileSerializer(serializers.Serializer):
    """Merchant panelidagi joriy xodim uchun o'z profili — merchant + filial ma'lumoti."""
    merchant_id = serializers.UUIDField(source="merchant.id", read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)
    merchant_type = serializers.CharField(source="merchant.type", read_only=True)
    merchant_description = serializers.CharField(source="merchant.description", read_only=True)
    merchant_status = serializers.CharField(source="merchant.status", read_only=True)
    merchant_logo = serializers.ImageField(source="merchant.logo", read_only=True, allow_null=True)
    merchant_cover = serializers.ImageField(source="merchant.cover", read_only=True, allow_null=True)
    position = serializers.CharField(read_only=True)
    branch = MerchantBranchSerializer(read_only=True)