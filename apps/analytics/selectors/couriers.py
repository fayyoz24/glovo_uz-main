from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from apps.couriers.models import CourierProfile
from apps.orders.models import Order


def get_courier_summary(start_date, end_date):
    delivered_orders = Order.objects.filter(
        created_at__gte=start_date, created_at__lte=end_date, status="delivered", courier__isnull=False
    )
    return {
        "total_couriers": CourierProfile.objects.count(),
        "active_couriers": CourierProfile.objects.filter(is_online=True).count(),
        "couriers_with_deliveries": delivered_orders.values("courier_id").distinct().count(),
    }


def get_top_couriers(start_date, end_date, limit=10):
    return list(
        Order.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date, status="delivered", courier__isnull=False
        )
        .values("courier_id", "courier__user__full_name")
        .annotate(delivered_orders=Count("id"))
        .order_by("-delivered_orders")[:limit]
    )


def get_courier_delivery_metrics(start_date, end_date):
    qs = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status="delivered",
        courier__isnull=False,
        picked_up_at__isnull=False,
        delivered_at__isnull=False,
    ).annotate(
        duration=ExpressionWrapper(F("delivered_at") - F("picked_up_at"), output_field=DurationField())
    )
    avg_duration = qs.aggregate(avg=Avg("duration"))["avg"]
    return {"avg_delivery_minutes": round(avg_duration.total_seconds() / 60, 2) if avg_duration else 0}
