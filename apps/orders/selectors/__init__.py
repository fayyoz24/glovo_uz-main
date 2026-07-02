from django.db.models import QuerySet
from apps.orders.models import Order
from apps.orders.constants import OrderStatus


def get_customer_orders(user, status: str = None) -> QuerySet:
    qs = (
        Order.objects.filter(customer=user)
        .select_related("merchant", "branch", "courier")
        .prefetch_related("items__modifiers", "status_history")
    )
    if status:
        qs = qs.filter(status=status)
    return qs


def get_order_for_customer(order_id, user) -> Order:
    return (
        Order.objects.filter(id=order_id, customer=user)
        .select_related("merchant", "branch", "courier")
        .prefetch_related("items__modifiers", "status_history")
        .get()
    )


def get_order_for_merchant(order_id, branch) -> Order:
    return (
        Order.objects.filter(id=order_id, branch=branch)
        .prefetch_related("items__modifiers")
        .get()
    )


def get_branch_orders(branch, status: str = None) -> QuerySet:
    qs = (
        Order.objects.filter(branch=branch)
        .select_related("customer", "courier")
        .prefetch_related("items")
    )
    if status:
        qs = qs.filter(status=status)
    return qs


def get_active_orders_for_courier(courier) -> QuerySet:
    active_statuses = [
        OrderStatus.COURIER_ASSIGNED,
        OrderStatus.PICKED_UP,
        OrderStatus.ON_THE_WAY,
    ]
    return (
        Order.objects.filter(courier=courier, status__in=active_statuses)
        .select_related("branch__merchant", "customer")
        .prefetch_related("items")
    )
