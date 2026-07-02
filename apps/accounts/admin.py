from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import (
    User,
    CustomerProfile,
    CourierProfile,
    MerchantStaffProfile,
    TelegramLoginCode,
    DeviceToken,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["telegram_username", "telegram_user_id", "full_name", "role", "is_verified", "is_active", "created_at"]
    list_filter = ["role", "is_active", "is_verified"]
    search_fields = ["telegram_username", "telegram_user_id", "phone", "full_name", "email"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("telegram_user_id", "telegram_username", "password")}),
        ("Personal info", {"fields": ("full_name", "phone", "email", "language")}),
        ("Permissions", {"fields": ("role", "is_active", "is_verified", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("telegram_user_id", "password1", "password2", "role")}),
    )


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "vehicle_type", "is_approved", "rating"]
    list_filter = ["vehicle_type", "is_approved"]


@admin.register(TelegramLoginCode)
class TelegramLoginCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "telegram_user_id", "telegram_username", "is_used", "attempts", "created_at", "expires_at"]
    list_filter = ["is_used"]
    search_fields = ["telegram_username", "telegram_user_id", "code"]


admin.site.register(CustomerProfile)
admin.site.register(MerchantStaffProfile)
admin.site.register(DeviceToken)
