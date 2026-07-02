import uuid
from django.db import models


class DailyAnalyticsSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)

    total_users = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    total_merchants = models.PositiveIntegerField(default=0)
    total_couriers = models.PositiveIntegerField(default=0)
    active_couriers = models.PositiveIntegerField(default=0)

    total_orders = models.PositiveIntegerField(default=0)
    delivered_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)

    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_orders_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    refunded_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    avg_order_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_delivery_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_daily_snapshot"
        ordering = ["-date"]

    def __str__(self):
        return f"Analytics Snapshot {self.date}"
