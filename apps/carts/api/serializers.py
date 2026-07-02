from rest_framework import serializers
from apps.carts.models import Cart, CartItem, CartItemModifier
from apps.catalog.api.serializers import ProductListSerializer, ModifierOptionSerializer


class CartItemModifierSerializer(serializers.ModelSerializer):
    name_ru = serializers.CharField(source="modifier_option.name_ru", read_only=True)
    name_uz = serializers.CharField(source="modifier_option.name_uz", read_only=True)

    class Meta:
        model = CartItemModifier
        fields = ["id", "modifier_option", "name_ru", "name_uz", "price", "qty"]
        read_only_fields = ["id", "name_ru", "name_uz"]


class CartItemSerializer(serializers.ModelSerializer):
    modifiers = CartItemModifierSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source="snapshot_name", read_only=True)
    variant_name = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_name", "variant", "variant_name",
            "qty", "unit_price", "line_total",
            "instructions", "modifiers",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "unit_price", "line_total", "created_at", "updated_at"]

    def get_variant_name(self, obj):
        return obj.variant.name_ru if obj.variant else None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    merchant_name = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id", "status", "branch", "branch_name", "merchant_name",
            "coupon_code", "subtotal", "discount_amount",
            "delivery_fee", "service_fee", "total",
            "expires_at", "item_count", "items",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.items.count()

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else None

    def get_merchant_name(self, obj):
        return obj.branch.merchant.name if obj.branch else None


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    qty = serializers.IntegerField(min_value=1, max_value=50, default=1)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    modifier_option_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )
    instructions = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")


class UpdateCartItemSerializer(serializers.Serializer):
    qty = serializers.IntegerField(min_value=1, max_value=50)


class ApplyPromoSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
