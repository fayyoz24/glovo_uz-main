from datetime import timedelta
from django.utils import timezone


class AnalyticsPeriod:
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    CUSTOM = "custom"

    CHOICES = (
        (TODAY, "Today"),
        (WEEK, "Week"),
        (MONTH, "Month"),
        (CUSTOM, "Custom"),
    )


class OrderStatus:
    PENDING = "pending"
    MERCHANT_CONFIRMED = "merchant_confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    COURIER_ASSIGNED = "courier_assigned"
    PICKED_UP = "picked_up"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus:
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


def resolve_period(period: str):
    now = timezone.now()
    if period == AnalyticsPeriod.TODAY:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == AnalyticsPeriod.WEEK:
        start = now - timedelta(days=7)
    elif period == AnalyticsPeriod.MONTH:
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=30)
    return start, now
