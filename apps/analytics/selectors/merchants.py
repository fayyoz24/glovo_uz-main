from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce

from apps.orders.models import Order
from apps.merchants.models import Merchant


def get_merchant_summary(start_date, end_date):
    merchants_with_orders = (
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .values("merchant_id")
        .distinct()
        .count()
    )
    return {"total_merchants": Merchant.objects.count(), "merchants_with_orders": merchants_with_orders}


def get_top_merchants_by_orders(start_date, end_date, limit=10):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .values("merchant_id", "merchant__name")
        .annotate(
            orders_count=Count("id"),
            delivered_count=Count("id", filter=Q(status="delivered")),
            cancelled_count=Count("id", filter=Q(status="cancelled")),
            revenue=Coalesce(Sum("total_amount", filter=Q(status="delivered")), Decimal("0.00")),
        )
        .order_by("-orders_count")[:limit]
    )


def get_top_merchants_by_revenue(start_date, end_date, limit=10):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date, status="delivered")
        .values("merchant_id", "merchant__name")
        .annotate(revenue=Coalesce(Sum("total_amount"), Decimal("0.00")), orders_count=Count("id"))
        .order_by("-revenue")[:limit]
    )


def get_low_performing_merchants(start_date, end_date, limit=10):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .values("merchant_id", "merchant__name")
        .annotate(
            orders_count=Count("id"),
            cancelled_count=Count("id", filter=Q(status="cancelled")),
            revenue=Coalesce(Sum("total_amount", filter=Q(status="delivered")), Decimal("0.00")),
        )
        .order_by("orders_count")[:limit]
    )
