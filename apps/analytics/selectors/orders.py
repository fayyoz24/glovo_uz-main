from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.db.models.functions import TruncDate

from apps.orders.models import Order


def get_orders_summary(start_date, end_date):
    qs = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    total = qs.count()
    delivered = qs.filter(status="delivered").count()
    cancelled = qs.filter(status="cancelled").count()
    pending = qs.filter(status="pending").count()
    return {
        "total_orders": total,
        "delivered_orders": delivered,
        "cancelled_orders": cancelled,
        "pending_orders": pending,
        "cancellation_rate": round((cancelled / total) * 100, 2) if total else 0,
    }


def get_orders_timeseries(start_date, end_date):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            total_orders=Count("id"),
            delivered_orders=Count("id", filter=Q(status="delivered")),
            cancelled_orders=Count("id", filter=Q(status="cancelled")),
        )
        .order_by("day")
    )


def get_avg_delivery_time(start_date, end_date):
    qs = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status="delivered",
        picked_up_at__isnull=False,
        delivered_at__isnull=False,
    ).annotate(
        duration=ExpressionWrapper(F("delivered_at") - F("picked_up_at"), output_field=DurationField())
    )
    avg_duration = qs.aggregate(avg=Avg("duration"))["avg"]
    return round(avg_duration.total_seconds() / 60, 2) if avg_duration else 0


def get_order_status_breakdown(start_date, end_date):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
