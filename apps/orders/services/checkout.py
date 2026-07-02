"""
Checkout xizmati — savat → buyurtmaga aylantirish.
Barcha operatsiyalar transaction.atomic ichida bajariladi.
"""
from django.db import transaction
from django.utils import timezone

from apps.carts.models import Cart, CartItem
from apps.carts.constants import CartStatus
from apps.carts.selectors import get_active_cart
from apps.orders.models import Order, OrderItem, OrderItemModifier, OrderStatusHistory
from apps.orders.constants import OrderStatus, PaymentMethod, PaymentStatus
from apps.orders.exceptions import EmptyCartError, BranchClosedError, CheckoutError


def _build_address_snapshot(address) -> dict:
    return {
        "id": str(address.id),
        "title": address.title,
        "address_line": address.address_line,
        "landmark": address.landmark,
        "entrance": address.entrance or "",
        "floor": address.floor or "",
        "apartment": address.apartment or "",
        "latitude": str(address.latitude) if address.latitude else None,
        "longitude": str(address.longitude) if address.longitude else None,
        "district": address.district,
        "city": address.city,
    }


def _validate_branch(branch):
    if not branch.is_open or not branch.accepting_orders:
        raise BranchClosedError()


def _create_order_items_from_cart(order: Order, cart: Cart):
    for cart_item in cart.items.prefetch_related("modifiers__modifier_option").all():
        order_item = OrderItem.objects.create(
            order=order,
            product_id=cart_item.product_id,
            product_name_snapshot=cart_item.snapshot_name or cart_item.product.name_uz,
            variant_snapshot=cart_item.variant.name_uz if cart_item.variant else "",
            qty=cart_item.qty,
            unit_price=cart_item.unit_price,
            line_total=cart_item.line_total,
            instructions=cart_item.instructions,
        )
        for mod in cart_item.modifiers.all():
            OrderItemModifier.objects.create(
                order_item=order_item,
                modifier_name=mod.modifier_option.name_uz,
                modifier_price=mod.price,
                qty=mod.qty,
            )


@transaction.atomic
def checkout_from_cart(
    *,
    user,
    address,
    payment_method: str,
    tip_amount=None,
) -> Order:
    from decimal import Decimal

    cart = get_active_cart(user)
    if cart is None or not cart.items.exists():
        raise EmptyCartError()

    branch = cart.branch
    _validate_branch(branch)

    if tip_amount is None:
        tip_amount = Decimal("0")

    # Narxni hisoblash
    subtotal = cart.subtotal
    delivery_fee = cart.delivery_fee
    service_fee = cart.service_fee
    discount_amount = cart.discount_amount
    total_amount = subtotal + delivery_fee + service_fee - discount_amount + tip_amount
    if total_amount < Decimal("0"):
        total_amount = Decimal("0")

    # COD bo'lsa payment_status = pending, aks holda ham pending (to'lov kelguncha)
    payment_status = PaymentStatus.PENDING

    order = Order.objects.create(
        customer=user,
        merchant=branch.merchant,
        branch=branch,
        address_snapshot=_build_address_snapshot(address),
        status=OrderStatus.PENDING,
        payment_method=payment_method,
        payment_status=payment_status,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        service_fee=service_fee,
        discount_amount=discount_amount,
        tip_amount=tip_amount,
        total_amount=total_amount,
        currency="UZS",
    )

    _create_order_items_from_cart(order, cart)

    # Holat tarixini boshlash
    OrderStatusHistory.objects.create(
        order=order,
        from_status="",
        to_status=OrderStatus.PENDING,
        changed_by=user,
        note="Buyurtma yaratildi",
    )

    # Savatni yopish
    cart.status = CartStatus.ORDERED
    cart.save(update_fields=["status", "updated_at"])

    # Async: merchantga bildirishnoma va dispatch pipeline ni ishga tushirish
    try:
        from apps.orders.tasks import notify_merchant_new_order
        notify_merchant_new_order.delay(str(order.id))
    except ImportError:
        pass

    return order
