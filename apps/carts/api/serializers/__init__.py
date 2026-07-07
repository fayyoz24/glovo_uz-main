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

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_name", "product_image",
            "variant", "qty", "unit_price", "line_total",
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
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

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

    def get_subtotal(self, obj):
        # Har doim items'dan jonli hisoblanadi — keshlangan cart.subtotal
        # maydoniga tayanmaymiz, chunki ba'zi holatlarda (masalan recalculate()
        # chaqirilmagan holatlar) u eskirib, items bilan mos kelmasligi mumkin.
        return sum(item.line_total for item in obj.items.all())

    def get_total(self, obj):
        subtotal = self.get_subtotal(obj)
        return subtotal + obj.delivery_fee + obj.service_fee - obj.discount_amount


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    qty = serializers.IntegerField(min_value=1, default=1)
    modifier_option_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    # allow_blank=True qo'shildi — bo'sh string ("") yuborilganda ham
    # 400 xato bermasligi kerak, chunki izoh ixtiyoriy.
    instructions = serializers.CharField(
        max_length=512, required=False, allow_blank=True, default=""
    )


class UpdateCartItemSerializer(serializers.Serializer):
    qty = serializers.IntegerField(min_value=0)


class ApplyPromoSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)