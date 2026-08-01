from decimal import Decimal

from rest_framework import serializers
from apps.carts.models import Cart, CartItem, CartItemModifier


class CartItemModifierSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="modifier_option.name_uz", read_only=True)

    class Meta:
        model = CartItemModifier
        fields = ["id", "name", "price", "qty"]


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name_uz", read_only=True)
    product_image = serializers.SerializerMethodField()
    modifiers = CartItemModifierSerializer(many=True, read_only=True)
    unit_type = serializers.CharField(source="product.unit_type", read_only=True)
    qty_step = serializers.DecimalField(source="product.qty_step", max_digits=8, decimal_places=2, read_only=True)
    qty_increments = serializers.ListField(source="product.qty_increments", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_name", "product_image",
            "variant", "qty", "unit_price", "line_total",
            "unit_type", "qty_step", "qty_increments",
            "modifiers", "instructions",
        ]

    def get_product_image(self, obj):
        first = obj.product.images.first()
        if first and first.image:
            return first.image.url
        return None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    merchant_name = serializers.CharField(source="branch.merchant.name", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id", "branch_name", "merchant_name", "status",
            "coupon_code", "subtotal", "discount_amount",
            "delivery_fee", "service_fee", "total",
            "item_count", "items",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    # DecimalField — dona mahsulotlar uchun butun (1, 2...), kg bilan
    # sotiladigan mahsulotlar uchun kasrli (0.1, 0.5...) qiymat qabul qilinadi.
    # Aniq qadam (0.1 yoki 0.5 ga karralilik) product.qty_step orqali servis
    # qatlamida tekshiriladi.
    qty = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0.1"), default=Decimal("1"))
    modifier_option_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    # allow_blank=True qo'shildi — bo'sh string ("") yuborilganda ham
    # 400 xato bermasligi kerak, chunki izoh ixtiyoriy.
    instructions = serializers.CharField(
        max_length=512, required=False, allow_blank=True, default=""
    )


class UpdateCartItemSerializer(serializers.Serializer):
    qty = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0"))


class ApplyPromoSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)