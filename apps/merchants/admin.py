from django.contrib import admin
from apps.merchants.models import Merchant, MerchantBranch, BranchWorkingHour


class BranchWorkingHourInline(admin.TabularInline):
    model = BranchWorkingHour
    extra = 0


class MerchantBranchInline(admin.TabularInline):
    model = MerchantBranch
    extra = 0
    show_change_link = True


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "status", "rating_avg", "created_at"]
    list_filter = ["type", "status"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MerchantBranchInline]


@admin.register(MerchantBranch)
class MerchantBranchAdmin(admin.ModelAdmin):
    list_display = ["merchant", "name", "is_open", "accepting_orders", "prep_time_min"]
    list_filter = ["is_open", "accepting_orders"]
    search_fields = ["merchant__name", "name", "address_text"]
    inlines = [BranchWorkingHourInline]
