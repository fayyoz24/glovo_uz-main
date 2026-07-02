from django.contrib import admin
from apps.couriers.models import CourierProfile, CourierLocationPing, CourierShift, CourierEarning


# @admin.register(CourierProfile)
# class CourierProfileAdmin(admin.ModelAdmin):
#     list_display = [
#         "user", "vehicle_type", "courier_status", "is_approved",
#         "rating", "total_deliveries", "balance",
#     ]
#     list_filter = ["courier_status", "vehicle_type", "is_approved"]
#     search_fields = ["user__phone", "user__full_name", "vehicle_number"]
#     list_editable = ["is_approved"]


@admin.register(CourierShift)
class CourierShiftAdmin(admin.ModelAdmin):
    list_display = ["courier", "start_time", "end_time", "status", "deliveries_count", "total_earned"]
    list_filter = ["status"]


@admin.register(CourierEarning)
class CourierEarningAdmin(admin.ModelAdmin):
    list_display = ["courier", "amount", "base_fee", "bonus", "tip", "created_at"]
    list_filter = ["created_at"]
