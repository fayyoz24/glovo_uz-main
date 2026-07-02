from rest_framework import serializers
from apps.orders.models import Order, OrderItem, OrderItemModifier, OrderStatusHistory
from apps.orders.constants import PaymentMethod


class OrderItemModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemModifier
        fields = ["modifier_name", "modifier_price", "qty"]


class OrderItemSerializer(serializers.ModelSerializer):
    modifiers = OrderItemModifierSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "product_id", "product_name_snapshot", "variant_snapshot",
            "qty", "unit_price", "line_total", "instructions", "modifiers",
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.full_name", read_only=True, default="")

    class Meta:
        model = OrderStatusHistory
        fields = ["from_status", "to_status", "changed_by_name", "note", "created_at"]


class OrderListSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "public_id", "merchant_name", "branch_name",
            "status", "payment_method", "payment_status",
            "total_amount", "currency", "placed_at", "item_count",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "public_id", "merchant_name", "branch_name",
            "status", "payment_method", "payment_status",
            "address_snapshot", "subtotal", "delivery_fee", "service_fee",
            "discount_amount", "tip_amount", "total_amount", "currency",
            "placed_at", "confirmed_at", "picked_up_at", "delivered_at",
            "cancel_reason", "cancel_note",
            "items", "status_history",
        ]


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    tip_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=50, required=False, default="customer_request")
    note = serializers.CharField(max_length=512, required=False, default="")


class MerchantOrderActionSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=512, required=False, default="")
