from django.contrib import admin
from apps.orders.models import Order, OrderItem, OrderItemModifier, OrderStatusHistory


class OrderItemModifierInline(admin.TabularInline):
    model = OrderItemModifier
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    inlines = []


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "note", "created_at"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "public_id", "customer", "merchant", "status",
        "payment_method", "payment_status", "total_amount", "placed_at",
    ]
    list_filter = ["status", "payment_method", "payment_status"]
    search_fields = ["public_id", "customer__phone", "customer__full_name"]
    readonly_fields = ["id", "public_id", "placed_at", "created_at", "updated_at"]
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["order", "from_status", "to_status", "changed_by", "created_at"]
    list_filter = ["to_status"]
    readonly_fields = ["created_at"]
