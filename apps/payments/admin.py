from django.contrib import admin
from django.utils.html import format_html

from apps.payments.models import PaymentTransaction, Refund


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "provider",
        "amount_display",
        "status",
        "paid_at",
        "created_at",
    ]
    list_filter = ["provider", "status", "currency"]
    search_fields = ["order__id", "provider_transaction_id"]
    readonly_fields = [
        "id",
        "order",
        "provider",
        "provider_transaction_id",
        "amount",
        "currency",
        "status",
        "payment_url",
        "raw_request",
        "raw_response",
        "extra",
        "paid_at",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} {obj.currency}"

    amount_display.short_description = "Amount"

    def has_add_permission(self, request):
        return False  # only created programmatically

    def has_delete_permission(self, request, obj=None):
        return False  # financial records must not be deleted


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "transaction", "amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["order__id", "transaction__id"]
    readonly_fields = [
        "id",
        "order",
        "transaction",
        "amount",
        "reason",
        "provider_response",
        "created_at",
        "updated_at",
        "processed_at",
    ]
    ordering = ["-created_at"]

    actions = ["approve_refunds"]

    def approve_refunds(self, request, queryset):
        from apps.payments.models import RefundStatus
        from apps.payments.services import process_refund

        processed = 0
        for refund in queryset.filter(status=RefundStatus.PENDING):
            try:
                process_refund(refund)
                processed += 1
            except Exception as e:
                self.message_user(request, f"Refund {refund.id}: {e}", level="error")

        self.message_user(request, f"{processed} ta refund qayta ishlandi.")

    approve_refunds.short_description = "Tanlangan refundlarni qayta ishlash"
