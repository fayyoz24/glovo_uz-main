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
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "public_id", "merchant_name", "branch_name",
            "status", "payment_method", "payment_status",
            "total_amount", "currency", "placed_at", "item_count", "items",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_lat = serializers.DecimalField(source="branch.latitude", max_digits=9, decimal_places=6, read_only=True)
    branch_lng = serializers.DecimalField(source="branch.longitude", max_digits=9, decimal_places=6, read_only=True)

    courier_id = serializers.UUIDField(source="courier.id", read_only=True, allow_null=True)
    courier_name = serializers.CharField(source="courier.full_name", read_only=True, allow_null=True)
    courier_phone = serializers.CharField(source="courier.phone", read_only=True, allow_null=True)
    courier_lat = serializers.SerializerMethodField()
    courier_lng = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()
    cancel_reason_display = serializers.CharField(source="get_cancel_reason_display", read_only=True)

    def get_courier_lat(self, obj):
        profile = getattr(obj.courier, "courier_profile", None) if obj.courier_id else None
        return profile.current_lat if profile else None

    def get_courier_lng(self, obj):
        profile = getattr(obj.courier, "courier_profile", None) if obj.courier_id else None
        return profile.current_lng if profile else None

    def get_has_review(self, obj):
        # Mijoz bu buyurtma uchun review qoldirganmi — qoldirgan bo'lsa
        # frontendda "Buyurtmani baholash" tugmasi ko'rsatilmaydi.
        # (OneToOne teskari bog'lanish yo'q bo'lsa, Django buni AttributeError
        # sifatida ko'taradi — shuning uchun hasattr() ishlatiladi.)
        return hasattr(obj, "review")

    class Meta:
        model = Order
        fields = [
            "id", "public_id", "merchant_name", "branch_name", "branch_lat", "branch_lng",
            "status", "payment_method", "payment_status",
            "address_snapshot", "subtotal", "delivery_fee", "service_fee",
            "discount_amount", "tip_amount", "total_amount", "currency",
            "placed_at", "confirmed_at", "picked_up_at", "delivered_at",
            "cancel_reason", "cancel_reason_display", "cancel_note",
            "courier_id", "courier_name", "courier_phone", "courier_lat", "courier_lng",
            "items", "status_history", "has_review",
        ]


# class CheckoutSerializer(serializers.Serializer):
#     address_id = serializers.IntegerField()
#     payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
#     tip_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
# # apps/orders/api/serializers.py

class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.UUIDField()
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    tip_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=50, required=False, default="customer_request")
    note = serializers.CharField(max_length=512, required=False, default="")


class MerchantOrderActionSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=512, required=False, default="")