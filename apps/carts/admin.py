from django.contrib import admin
from apps.carts.models import Cart, CartItem, CartItemModifier


class CartItemModifierInline(admin.TabularInline):
    model = CartItemModifier
    extra = 0


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    show_change_link = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "branch", "subtotal", "total", "expires_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__phone"]
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["snapshot_name", "cart", "qty", "unit_price", "line_total"]
    search_fields = ["snapshot_name", "cart__user__phone"]
    inlines = [CartItemModifierInline]
