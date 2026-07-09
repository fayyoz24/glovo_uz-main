from rest_framework import serializers
from apps.catalog.models import (
    ProductCategory,
    Product,
    ProductVariant,
    ProductModifierGroup,
    ProductModifierOption,
)


class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    merchant_type_code = serializers.CharField(source="merchant_type.code", read_only=True)

    class Meta:
        model = ProductCategory
        fields = (
            "id",
            "parent",
            "merchant_type",
            "merchant_type_code",
            "name_uz",
            "name_ru",
            "name_en",
            "icon",
            "sort_order",
            "children",
        )

    def get_children(self, obj):
        qs = obj.children.filter(is_active=True)
        return ProductCategorySerializer(qs, many=True).data


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "name_uz",
            "name_ru",
            "name_en",
            "price_delta",
            "final_price",
            "is_default",
            "is_active",
            "sort_order",
        )


class ModifierOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModifierOption
        fields = (
            "id",
            "name_uz",
            "name_ru",
            "price_delta",
            "is_active",
            "sort_order",
        )


class ModifierGroupSerializer(serializers.ModelSerializer):
    options = ModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductModifierGroup
        fields = (
            "id",
            "name_uz",
            "name_ru",
            "group_type",
            "min_select",
            "max_select",
            "required",
            "sort_order",
            "options",
        )


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight — catalog grid uchun. Customerga ikkala narx (asl va chegirmali) ko'rinadi."""
    category_name = serializers.CharField(source="category.name_uz", read_only=True)
    base_price_display = serializers.IntegerField(source="base_price", read_only=True)
    discounted_price = serializers.IntegerField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name_uz",
            "name_ru",
            "image",
            "base_price_display",
            "discount_percent",
            "discounted_price",
            "has_discount",
            "is_available",
            "in_stock",
            "category_name",
            "sort_order",
        )

    def get_in_stock(self, obj):
        return (not obj.track_stock) or obj.stock_qty > 0


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full detail — product page uchun."""
    variants = ProductVariantSerializer(many=True, read_only=True)
    modifier_groups = ModifierGroupSerializer(many=True, read_only=True)
    category = ProductCategorySerializer(read_only=True)
    base_price_display = serializers.IntegerField(source="base_price", read_only=True)
    discounted_price = serializers.IntegerField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "merchant",
            "branch",
            "category",
            "name_uz",
            "name_ru",
            "name_en",
            "description_uz",
            "description_ru",
            "image",
            "base_price_display",
            "discount_percent",
            "discounted_price",
            "has_discount",
            "sku",
            "status",
            "is_active",
            "is_available",
            "stock_qty",
            "track_stock",
            "in_stock",
            "variants",
            "modifier_groups",
            "sort_order",
            "created_at",
            "updated_at",
        )

    def get_in_stock(self, obj):
        return (not obj.track_stock) or obj.stock_qty > 0


class ProductCreateSerializer(serializers.ModelSerializer):
    """Merchant panel — yangi mahsulot qo'shish."""

    class Meta:
        model = Product
        fields = (
            "branch",
            "category",
            "name_uz",
            "name_ru",
            "name_en",
            "description_uz",
            "description_ru",
            "base_price",
            "sku",
            "image",
            "discount_percent",
            "track_stock",
            "stock_qty",
        )
        extra_kwargs = {
            "name_en": {"required": False},
            "description_uz": {"required": False},
            "description_ru": {"required": False},
            "sku": {"required": False},
            "branch": {"required": False},
            "category": {"required": False},
            "image": {"required": False},
            "discount_percent": {"required": False},
            "track_stock": {"required": False},
            "stock_qty": {"required": False},
        }

    def validate_discount_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Chegirma foizi 0 dan 100 gacha bo'lishi kerak.")
        return value


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "category",
            "name_uz",
            "name_ru",
            "name_en",
            "description_uz",
            "description_ru",
            "base_price",
            "sku",
            "image",
            "discount_percent",
            "track_stock",
            "stock_qty",
            "is_active",
            "is_available",
            "sort_order",
        )

        extra_kwargs = {
            field: {"required": False}
            for field in fields
        }

    def validate_discount_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Chegirma foizi 0 dan 100 gacha bo'lishi kerak.")
        return value
