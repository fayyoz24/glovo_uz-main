from django.contrib import admin

from apps.promotions.models import PromoCampaign, PromoUsage, ReferralCode, ReferralUsage


@admin.register(PromoCampaign)
class PromoCampaignAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "discount_type",
        "discount_value",
        "status",
        "usage_count",
        "usage_limit",
        "starts_at",
        "ends_at",
    ]
    list_filter = ["status", "discount_type", "target_type"]
    search_fields = ["code", "name"]
    readonly_fields = ["usage_count", "created_at", "updated_at"]
    ordering = ["-created_at"]
    fieldsets = (
        (
            "Asosiy ma'lumot",
            {
                "fields": ("name", "description", "code", "status"),
            },
        ),
        (
            "Chegirma sozlamalari",
            {
                "fields": (
                    "discount_type",
                    "discount_value",
                    "max_discount",
                    "min_order_amount",
                    "applies_to_delivery_fee",
                    "is_combinable",
                ),
            },
        ),
        (
            "Foydalanish limiti",
            {
                "fields": ("usage_limit", "per_user_limit", "usage_count"),
            },
        ),
        (
            "Vaqt oralig'i",
            {
                "fields": ("starts_at", "ends_at"),
            },
        ),
        (
            "Maqsadli auditoriya",
            {
                "fields": ("target_type", "merchant", "allowed_users"),
            },
        ),
        (
            "Meta",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PromoUsage)
class PromoUsageAdmin(admin.ModelAdmin):
    list_display = ["promo", "user", "order", "discount_amount_applied", "used_at"]
    list_filter = ["used_at"]
    search_fields = ["promo__code", "user__phone"]
    readonly_fields = ["used_at"]


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "user", "use_count", "max_uses", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["code", "user__phone"]
    readonly_fields = ["use_count", "created_at"]


@admin.register(ReferralUsage)
class ReferralUsageAdmin(admin.ModelAdmin):
    list_display = [
        "referral_code",
        "referee",
        "referrer_bonus_credited",
        "referee_bonus_credited",
        "used_at",
    ]
    list_filter = ["referrer_bonus_credited", "referee_bonus_credited"]
    search_fields = ["referral_code__code", "referee__phone"]
    readonly_fields = ["used_at"]
