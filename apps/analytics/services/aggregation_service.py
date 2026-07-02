from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.analytics.models import DailyAnalyticsSnapshot
from apps.analytics.selectors.dashboard import get_dashboard_overview, get_dashboard_delivery_metrics
from apps.analytics.selectors.revenue import get_revenue_summary


class AnalyticsAggregationService:
    @classmethod
    @transaction.atomic
    def build_daily_snapshot(cls, date=None):
        if date is None:
            date = timezone.localdate()

        start_dt = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.max.time()))

        overview = get_dashboard_overview(start_dt, end_dt)
        revenue = get_revenue_summary(start_dt, end_dt)
        delivery = get_dashboard_delivery_metrics(start_dt, end_dt)

        snapshot, _ = DailyAnalyticsSnapshot.objects.update_or_create(
            date=date,
            defaults={
                "total_users": overview["users_total"],
                "total_customers": overview["customers_total"],
                "total_merchants": overview["merchants_total"],
                "total_couriers": overview["couriers_total"],
                "active_couriers": overview["active_couriers"],
                "total_orders": overview["total_orders"],
                "delivered_orders": overview["delivered_orders"],
                "cancelled_orders": overview["cancelled_orders"],
                "gross_revenue": revenue["gross_revenue"],
                "paid_orders_amount": revenue["paid_amount"],
                "refunded_amount": revenue["refunded_amount"],
                "avg_order_value": revenue["avg_order_value"],
                "avg_delivery_minutes": Decimal(str(delivery["avg_delivery_minutes"] or 0)),
            },
        )
        return snapshot
