from rest_framework import serializers
from apps.dispatch.models import CourierAssignment


class OrderOfferSerializer(serializers.ModelSerializer):
    """Kuryerga ko'rsatiladigan buyurtma taklifi."""
    order_id = serializers.UUIDField(source="order.id", read_only=True)
    public_id = serializers.CharField(source="order.public_id", read_only=True)
    merchant_name = serializers.CharField(source="order.merchant.name", read_only=True)
    branch_name = serializers.CharField(source="order.branch.name", read_only=True)
    branch_address = serializers.CharField(source="order.branch.address_text", read_only=True)
    delivery_address = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        source="order.total_amount", max_digits=14, decimal_places=2, read_only=True
    )
    payment_method = serializers.CharField(source="order.payment_method", read_only=True)
    item_count = serializers.SerializerMethodField()
    expires_in_seconds = serializers.SerializerMethodField()

    class Meta:
        model = CourierAssignment
        fields = [
            "id", "order_id", "public_id", "merchant_name",
            "branch_name", "branch_address", "delivery_address",
            "total_amount", "payment_method", "distance_km",
            "item_count", "expires_in_seconds", "status",
        ]

    def get_delivery_address(self, obj):
        snap = obj.order.address_snapshot
        return snap.get("address_line", "") if snap else ""

    def get_item_count(self, obj):
        return obj.order.items.count()

    def get_expires_in_seconds(self, obj):
        from django.utils import timezone
        delta = obj.offer_expires_at - timezone.now()
        return max(int(delta.total_seconds()), 0)


class AssignmentActionSerializer(serializers.Serializer):
    """Qabul qilish yoki rad etish uchun."""
    pass  # Hozirda qo'shimcha maydon kerak emas


class CourierAssignmentListSerializer(serializers.ModelSerializer):
    order_public_id = serializers.CharField(source="order.public_id", read_only=True)
    merchant_name = serializers.CharField(source="order.merchant.name", read_only=True)

    class Meta:
        model = CourierAssignment
        fields = [
            "id", "order_public_id", "merchant_name",
            "status", "attempt_number", "distance_km",
            "assigned_at", "accepted_at", "completed_at",
        ]
