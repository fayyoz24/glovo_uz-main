from django.contrib import admin
from apps.merchants.models import Merchant, MerchantBranch, BranchWorkingHour, MerchantStaffProfile, MerchantType
from apps.merchants.services import approve_merchant, reject_merchant


@admin.register(MerchantType)
class MerchantTypeAdmin(admin.ModelAdmin):
    list_display = ["name_uz", "code", "sort_order", "is_active"]
    search_fields = ["name_uz", "name_ru", "code"]


class BranchWorkingHourInline(admin.TabularInline):
    model = BranchWorkingHour
    extra = 0


class MerchantBranchInline(admin.TabularInline):
    model = MerchantBranch
    extra = 0
    show_change_link = True


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "status", "owner", "rating_avg", "created_at"]
    list_filter = ["type", "status"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MerchantBranchInline]
    actions = ["approve_merchants", "reject_merchants"]

    @admin.action(description="Tanlangan do'konlarni tasdiqlash (approve)")
    def approve_merchants(self, request, queryset):
        count = 0
        for merchant in queryset:
            approve_merchant(merchant)
            count += 1
        self.message_user(request, f"{count} ta do'kon tasdiqlandi.")

    @admin.action(description="Tanlangan do'konlarni rad etish (reject)")
    def reject_merchants(self, request, queryset):
        count = 0
        for merchant in queryset:
            reject_merchant(merchant)
            count += 1
        self.message_user(request, f"{count} ta do'kon rad etildi.")


@admin.register(MerchantBranch)
class MerchantBranchAdmin(admin.ModelAdmin):
    list_display = ["merchant", "name", "is_open", "accepting_orders", "prep_time_min"]
    list_filter = ["is_open", "accepting_orders"]
    search_fields = ["merchant__name", "name", "address_text"]
    inlines = [BranchWorkingHourInline]


@admin.register(MerchantStaffProfile)
class MerchantStaffProfileAdmin(admin.ModelAdmin):
    """
    Merchant Panelga kirish shu yozuv orqali beriladi (user <-> merchant bog'lanishi).
    Odatda bu avtomatik `approve_merchants` action orqali yaratiladi — bu yerda
    faqat ko'rish yoki qo'lda tuzatish (masalan xato bog'langan holatlarni) uchun.
    """
    list_display = ["user", "merchant", "branch", "position", "is_active", "created_at"]
    list_filter = ["is_active", "position"]
    search_fields = ["user__phone", "user__full_name", "merchant__name"]
    autocomplete_fields = ["user", "merchant", "branch"]
