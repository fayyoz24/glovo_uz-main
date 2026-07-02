from rest_framework import serializers
from apps.couriers.models import CourierProfile, CourierLocationPing, CourierShift, CourierEarning


class CourierProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = CourierProfile
        fields = [
            "id", "full_name", "phone", "vehicle_type", "vehicle_number",
            "courier_status", "is_approved", "rating", "total_deliveries",
            "balance", "current_lat", "current_lng", "last_location_at",
        ]
        read_only_fields = [
            "courier_status", "is_approved", "rating",
            "total_deliveries", "balance", "current_lat",
            "current_lng", "last_location_at",
        ]


class CourierProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourierProfile
        fields = ["vehicle_type", "vehicle_number", "photo"]


class LocationPingSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    accuracy = serializers.FloatField(required=False, allow_null=True)


class CourierShiftSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourierShift
        fields = [
            "id", "start_time", "end_time", "status",
            "deliveries_count", "total_earned", "duration_minutes",
        ]


class CourierEarningSerializer(serializers.ModelSerializer):
    order_public_id = serializers.CharField(source="order.public_id", read_only=True, default="")

    class Meta:
        model = CourierEarning
        fields = [
            "id", "order_public_id", "amount", "base_fee",
            "bonus", "tip", "note", "created_at",
        ]


class EarningsSummarySerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    base_fee = serializers.DecimalField(max_digits=14, decimal_places=2)
    bonus = serializers.DecimalField(max_digits=14, decimal_places=2)
    tips = serializers.DecimalField(max_digits=14, decimal_places=2)
    deliveries = serializers.IntegerField()
    period_days = serializers.IntegerField()
