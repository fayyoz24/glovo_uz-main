from apps.analytics.models import DailyAnalyticsSnapshot
from datetime import timedelta
from django.utils import timezone
import random

self.stdout.write("DailyAnalyticsSnapshot yaratilmoqda...")

for i in range(50):
    DailyAnalyticsSnapshot.objects.get_or_create(
        date=timezone.now().date() - timedelta(days=i),
        defaults={
            "total_users": random.randint(100, 10000),
            "total_customers": random.randint(50, 8000),
            "total_merchants": random.randint(10, 500),
            "total_couriers": random.randint(20, 1000),
            "active_couriers": random.randint(10, 500),

            "total_orders": random.randint(100, 10000),
            "delivered_orders": random.randint(50, 9000),
            "cancelled_orders": random.randint(0, 500),

            "gross_revenue": random.randint(1_000_000, 50_000_000),
            "paid_orders_amount": random.randint(500_000, 40_000_000),
            "refunded_amount": random.randint(0, 3_000_000),

            "avg_order_value": random.randint(30_000, 250_000),
            "avg_delivery_minutes": round(random.uniform(10, 60), 2),
        },
    )

self.stdout.write(
    self.style.SUCCESS("50 ta DailyAnalyticsSnapshot yaratildi.")
)