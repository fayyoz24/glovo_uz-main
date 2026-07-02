from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce

from apps.accounts.models import User
from apps.orders.models import Order
from apps.payments.models import PaymentTransaction
from apps.merchants.models import Merchant
from apps.couriers.models import CourierProfile


def get_dashboard_overview(start_date, end_date):
    users_total = User.objects.count()
    customers_total = User.objects.filter(role="customer").count()
    merchants_total = Merchant.objects.count()
    couriers_total = CourierProfile.objects.count()
    active_couriers = CourierProfile.objects.filter(is_online=True).count()

    orders_qs = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

    total_orders = orders_qs.count()
    delivered_orders = orders_qs.filter(status="delivered").count()
    cancelled_orders = orders_qs.filter(status="cancelled").count()

    gross_revenue = orders_qs.filter(status="delivered").aggregate(
        total=Coalesce(Sum("total_amount"), Decimal("0.00"))
    )["total"]

    avg_order_value = orders_qs.aggregate(
        avg=Coalesce(Avg("total_amount"), Decimal("0.00"))
    )["avg"]

    cancellation_rate = round((cancelled_orders / total_orders) * 100, 2) if total_orders else 0

    return {
        "users_total": users_total,
        "customers_total": customers_total,
        "merchants_total": merchants_total,
        "couriers_total": couriers_total,
        "active_couriers": active_couriers,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "gross_revenue": gross_revenue,
        "avg_order_value": avg_order_value,
        "cancellation_rate": cancellation_rate,
    }


def get_dashboard_order_status_breakdown(start_date, end_date):
    return list(
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def get_dashboard_payment_summary(start_date, end_date):
    qs = PaymentTransaction.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

    total_transactions = qs.count()
    paid_count = qs.filter(status="paid").count()
    failed_count = qs.filter(status="failed").count()
    refunded_count = qs.filter(status__in=["refunded", "partially_refunded"]).count()

    paid_amount = qs.filter(status="paid").aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    refunded_amount = qs.filter(status__in=["refunded", "partially_refunded"]).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    success_rate = round((paid_count / total_transactions) * 100, 2) if total_transactions else 0

    by_provider = list(
        qs.values("provider").annotate(
            total_transactions=Count("id"),
            paid_transactions=Count("id", filter=Q(status="paid")),
            paid_amount=Coalesce(Sum("amount", filter=Q(status="paid")), Decimal("0.00")),
        ).order_by("provider")
    )

    return {
        "total_transactions": total_transactions,
        "paid_count": paid_count,
        "failed_count": failed_count,
        "refunded_count": refunded_count,
        "paid_amount": paid_amount,
        "refunded_amount": refunded_amount,
        "success_rate": success_rate,
        "by_provider": by_provider,
    }


def get_dashboard_delivery_metrics(start_date, end_date):
    qs = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status="delivered",
        picked_up_at__isnull=False,
        delivered_at__isnull=False,
    ).annotate(
        delivery_duration=ExpressionWrapper(
            F("delivered_at") - F("picked_up_at"),
            output_field=DurationField(),
        )
    )

    avg_delivery_duration = qs.aggregate(avg=Avg("delivery_duration"))["avg"]
    avg_delivery_minutes = round(avg_delivery_duration.total_seconds() / 60, 2) if avg_delivery_duration else 0

    return {"avg_delivery_minutes": avg_delivery_minutes}
