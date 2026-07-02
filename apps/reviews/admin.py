from django.contrib import admin

from apps.reviews.models import Review, ReviewFlag, ReviewImage


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    readonly_fields = ["image", "sort_order", "created_at"]


class ReviewFlagInline(admin.TabularInline):
    model = ReviewFlag
    extra = 0
    readonly_fields = ["flagged_by", "reason", "note", "created_at"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "merchant",
        "customer",
        "merchant_rating",
        "courier_rating",
        "status",
        "flag_count",
        "created_at",
    ]
    list_filter = ["status", "merchant_rating", "courier_rating"]
    search_fields = ["merchant__name", "customer__phone", "merchant_comment"]
    readonly_fields = ["id", "flag_count", "created_at", "updated_at"]
    ordering = ["-created_at"]
    inlines = [ReviewImageInline, ReviewFlagInline]

    actions = ["hide_selected", "restore_selected"]

    def hide_selected(self, request, queryset):
        from reviews.constants import ReviewStatus
        queryset.update(status=ReviewStatus.HIDDEN)
    hide_selected.short_description = "Tanlangan reviewlarni yashirish"

    def restore_selected(self, request, queryset):
        from reviews.constants import ReviewStatus
        queryset.update(status=ReviewStatus.VISIBLE, flag_count=0)
    restore_selected.short_description = "Tanlangan reviewlarni tiklash"


@admin.register(ReviewFlag)
class ReviewFlagAdmin(admin.ModelAdmin):
    list_display = ["review", "flagged_by", "reason", "created_at"]
    list_filter = ["reason"]
    search_fields = ["review__id", "flagged_by__phone"]
    readonly_fields = ["created_at"]
