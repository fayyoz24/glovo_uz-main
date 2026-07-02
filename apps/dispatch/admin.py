from django.contrib import admin
from apps.dispatch.models import CourierAssignment


@admin.register(CourierAssignment)
class CourierAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "order", "courier", "status", "attempt_number",
        "distance_km", "assigned_at", "accepted_at",
    ]
    list_filter = ["status", "attempt_number"]
    search_fields = ["order__public_id", "courier__phone"]
    readonly_fields = ["id", "assigned_at"]
