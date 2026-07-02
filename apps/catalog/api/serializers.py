from rest_framework import serializers
from apps.catalog.models import (
    ProductCategory,
    Product,
    ProductImage,
    ProductVariant,
    ProductModifierGroup,
    ProductModifierOption,
)


# class ProductCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductCategory
#         fields = ["id", "parent", "name_uz", "name_ru", "name_en", "icon", "sort_order"]
#         read_only_fields = ["id"]


# class ProductImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductImage
#         fields = ["id", "image", "sort_order"]
#         read_only_fields = ["id"]


# class ProductVariantSerializer(serializers.ModelSerializer):
#     final_price = serializers.IntegerField(read_only=True)

#     class Meta:
#         model = ProductVariant
#         fields = [
#             "id", "name_uz", "name_ru", "name_en",
#             "price_delta", "final_price", "is_default",
#             "is_active", "sort_order",
#         ]
#         read_only_fields = ["id", "final_price"]


# class ModifierOptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductModifierOption
#         fields = ["id", "name_uz", "name_ru", "price_delta", "is_active", "sort_order"]
#         read_only_fields = ["id"]


# class ModifierGroupSerializer(serializers.ModelSerializer):
#     options = ModifierOptionSerializer(many=True, read_only=True)

#     class Meta:
#         model = ProductModifierGroup
#         fields = [
#             "id", "name_uz", "name_ru", "group_type",
#             "min_select", "max_select", "required",
#             "sort_order", "options",
#         ]
#         read_only_fields = ["id"]


# class ProductListSerializer(serializers.ModelSerializer):
#     """Lightweight — catalog grid uchun."""
#     cover_image = serializers.SerializerMethodField()

#     class Meta:
#         model = Product
#         fields = [
#             "id", "name_uz", "name_ru", "base_price",
#             "is_available", "cover_image", "sort_order",
#         ]

#     def get_cover_image(self, obj):
#         first = obj.images.first()
#         if first:
#             request = self.context.get("request")
#             return request.build_absolute_uri(first.image.url) if request else first.image.url
#         return None





# class ProductWriteSerializer(serializers.ModelSerializer):
#     """Merchant panel — product yaratish/tahrirlash."""
#     class Meta:
#         model = Product
#         fields = [
#             "branch", "category",
#             "name_uz", "name_ru", "name_en",
#             "description_uz", "description_ru",
#             "base_price", "sku", "is_active", "is_available", "sort_order",
#         ]

# from rest_framework import serializers
# from apps.catalog.models import (
#     ProductCategory,
#     Product,
#     ProductImage,
#     ProductVariant,
#     ProductModifierGroup,
#     ProductModifierOption,
# )


# class ProductCategorySerializer(serializers.ModelSerializer):
#     children = serializers.SerializerMethodField()

#     class Meta:
#         model = ProductCategory
#         fields = ["id", "parent", "name_uz", "name_ru", "icon", "sort_order", "children"]

#     def get_children(self, obj):
#         if obj.children.exists():
#             return ProductCategorySerializer(obj.children.filter(is_active=True), many=True).data
#         return []


# class ProductImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductImage
#         fields = ["id", "image", "sort_order"]


# class ProductVariantSerializer(serializers.ModelSerializer):
#     final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

#     class Meta:
#         model = ProductVariant
#         fields = ["id", "name_uz", "name_ru", "price_delta", "final_price", "is_default"]


# class ProductModifierOptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductModifierOption
#         fields = ["id", "name_uz", "name_ru", "price_delta"]


# class ProductModifierGroupSerializer(serializers.ModelSerializer):
#     options = ProductModifierOptionSerializer(many=True, read_only=True)

#     class Meta:
#         model = ProductModifierGroup
#         fields = ["id", "name_uz", "name_ru", "group_type", "min_select", "max_select", "required", "options"]


# class ProductListSerializer(serializers.ModelSerializer):
#     images = ProductImageSerializer(many=True, read_only=True)
#     category_name = serializers.CharField(source="category.name_uz", read_only=True)

#     class Meta:
#         model = Product
#         fields = [
#             "id", "name_uz", "name_ru", "base_price", "is_available",
#             "category_name", "images", "sort_order",
#         ]


# class ProductDetailSerializer(serializers.ModelSerializer):
#     images = ProductImageSerializer(many=True, read_only=True)
#     variants = ProductVariantSerializer(many=True, read_only=True)
#     modifier_groups = ProductModifierGroupSerializer(many=True, read_only=True)
#     category = ProductCategorySerializer(read_only=True)

#     class Meta:
#         model = Product
#         fields = [
#             "id", "name_uz", "name_ru", "description_uz", "description_ru",
#             "base_price", "is_active", "is_available", "sku",
#             "category", "images", "variants", "modifier_groups",
#         ]
# class ProductDetailSerializer(serializers.ModelSerializer):
#     """Full detail — product page uchun."""
#     images = ProductImageSerializer(many=True, read_only=True)
#     variants = ProductVariantSerializer(many=True, read_only=True)
#     modifier_groups = ModifierGroupSerializer(many=True, read_only=True)
#     category = ProductCategorySerializer(read_only=True)

#     class Meta:
#         model = Product
#         fields = [
#             "id", "merchant", "branch", "category",
#             "name_uz", "name_ru", "name_en",
#             "description_uz", "description_ru",
#             "base_price", "sku", "status",
#             "is_active", "is_available",
#             "images", "variants", "modifier_groups",
#             "sort_order", "created_at", "updated_at",
#         ]
#         read_only_fields = ["id", "created_at", "updated_at"]

# class ProductCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = [
#             "merchant", "branch", "category", "name_uz", "name_ru",
#             "description_uz", "description_ru", "base_price", "sku",
#         ]


# class ProductUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = [
#             "category", "name_uz", "name_ru", "description_uz",
#             "description_ru", "base_price", "is_active", "is_available",
#             "sku", "sort_order",
#         ]
#         extra_kwargs = {field: {"required": False} for field in fields}

#GPT variant
class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = (
            "id",
            "parent",
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


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "image",
            "sort_order",
        )

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
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(
        source="category.name_uz",
        read_only=True,
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "name_uz",
            "name_ru",
            "base_price",
            "is_available",
            "category_name",
            "images",
            "sort_order",
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    modifier_groups = ModifierGroupSerializer(many=True, read_only=True)
    category = ProductCategorySerializer(read_only=True)

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
            "base_price",
            "sku",
            "status",
            "is_active",
            "is_available",
            "images",
            "variants",
            "modifier_groups",
            "sort_order",
            "created_at",
            "updated_at",
        )


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "merchant",
            "branch",
            "category",
            "name_uz",
            "name_ru",
            "name_en",
            "description_uz",
            "description_ru",
            "base_price",
            "sku",
        )

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
            "is_active",
            "is_available",
            "sort_order",
        )

        extra_kwargs = {
            field: {"required": False}
            for field in fields
        }