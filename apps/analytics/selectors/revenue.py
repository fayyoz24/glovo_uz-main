from decimal import Decimal
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDate, Coalesce

from apps.orders.models import Order
from apps.payments.models import PaymentTransaction


def get_revenue_summary(start_date, end_date):
    delivered_orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date, status="delivered")
    gross_revenue = delivered_orders.aggregate(total=Coalesce(Sum("total_amount"), Decimal("0.00")))["total"]
    avg_order_value = delivered_orders.aggregate(avg=Coalesce(Avg("total_amount"), Decimal("0.00")))["avg"]

    tx_qs = PaymentTransaction.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    paid_amount = tx_qs.filter(status="paid").aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))["total"]
    refunded_amount = tx_qs.filter(status__in=["refunded", "partially_refunded"]).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    return {
        "gross_revenue": gross_revenue,
        "paid_amount": paid_amount,
        "refunded_amount": refunded_amount,
        "avg_order_value": avg_order_value,
    }


def get_revenue_by_day(start_date, end_date):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date, status="delivered")
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Coalesce(Sum("total_amount"), Decimal("0.00")), orders_count=Count("id"))
        .order_by("day")
    )


def get_payment_provider_breakdown(start_date, end_date):
    return list(
        PaymentTransaction.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .values("provider")
        .annotate(
            total_transactions=Count("id"),
            paid_transactions=Count("id", filter=Q(status="paid")),
            paid_amount=Coalesce(Sum("amount", filter=Q(status="paid")), Decimal("0.00")),
        )
        .order_by("provider")
    )
