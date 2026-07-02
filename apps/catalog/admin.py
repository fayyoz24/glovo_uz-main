from django.contrib import admin
from apps.catalog.models import (
    ProductCategory, Product, ProductImage,
    ProductVariant, ProductModifierGroup, ProductModifierOption,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ModifierOptionInline(admin.TabularInline):
    model = ProductModifierOption
    extra = 0


class ModifierGroupInline(admin.TabularInline):
    model = ProductModifierGroup
    extra = 0
    show_change_link = True


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "parent", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name_ru", "name_uz"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "merchant", "base_price", "status", "is_available", "created_at"]
    list_filter = ["status", "is_active", "is_available"]
    search_fields = ["name_ru", "name_uz", "sku"]
    inlines = [ProductImageInline, ProductVariantInline, ModifierGroupInline]


@admin.register(ProductModifierGroup)
class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "product", "group_type", "min_select", "max_select", "required"]
    inlines = [ModifierOptionInline]
