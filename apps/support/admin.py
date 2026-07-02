from django.contrib import admin
from django.utils.html import format_html

from apps.support.models import Complaint, ComplaintMessage, Dispute, RefundRequest


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = [
        "public_id",
        "customer",
        "complaint_type",
        "priority",
        "status",
        "assigned_to",
        "created_at",
    ]
    list_filter = ["status", "complaint_type", "priority"]
    search_fields = ["public_id", "subject", "customer__phone"]
    readonly_fields = ["public_id", "created_at", "updated_at"]
    raw_id_fields = ["customer", "assigned_to"]
    ordering = ["-created_at"]


@admin.register(ComplaintMessage)
class ComplaintMessageAdmin(admin.ModelAdmin):
    list_display = ["complaint", "sender_type", "is_internal", "created_at"]
    list_filter = ["sender_type", "is_internal"]
    search_fields = ["complaint__public_id", "body"]
    readonly_fields = ["created_at"]


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ["id", "order_id", "raised_by", "status", "assigned_to", "created_at"]
    list_filter = ["status"]
    search_fields = ["order_id"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["raised_by", "assigned_to", "complaint"]
    ordering = ["-created_at"]


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order_id",
        "customer",
        "reason",
        "amount",
        "status",
        "reviewed_by",
        "created_at",
    ]
    list_filter = ["status", "reason"]
    search_fields = ["order_id", "customer__phone"]
    readonly_fields = ["created_at", "updated_at", "processed_at"]
    raw_id_fields = ["customer", "reviewed_by", "complaint"]
    ordering = ["-created_at"]
