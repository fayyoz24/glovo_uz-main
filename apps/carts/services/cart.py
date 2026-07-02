from django.db import transaction
from django.utils import timezone

from apps.carts.models import Cart, CartItem, CartItemModifier
from apps.carts.constants import CartStatus, MAX_CART_ITEM_QTY
from apps.carts.selectors import get_active_cart
from apps.carts.exceptions import (
    CartNotFound,
    CartExpired,
    CartItemNotFound,
    BranchMismatch,
    InvalidQuantity,
    InvalidPromoCode,
    PromoMinOrderNotMet,
    CartEmpty,
)
from apps.catalog.models import Product, ProductVariant
from apps.catalog.exceptions import ProductNotAvailable, InvalidVariant
from apps.catalog.services import validate_modifier_selection


def get_or_create_active_cart(user, branch_id=None) -> Cart:
    """Get existing active cart or create a new one."""
    cart = get_active_cart(user)
    if cart:
        if cart.is_expired:
            cart.status = CartStatus.EXPIRED
            cart.save(update_fields=["status"])
            cart = None
    if not cart:
        cart = Cart.objects.create(user=user, branch_id=branch_id)
    return cart


def add_item_to_cart(
    user,
    product_id,
    qty: int,
    variant_id=None,
    modifier_option_ids: list = None,
    instructions: str = "",
) -> CartItem:
    if qty < 1 or qty > MAX_CART_ITEM_QTY:
        raise InvalidQuantity()

    product = Product.objects.filter(id=product_id).select_related("merchant").first()
    if not product or not product.is_orderable:
        raise ProductNotAvailable()

    # Resolve branch from product
    branch = product.branch or product.merchant.branches.filter(
        is_open=True, accepting_orders=True
    ).first()

    with transaction.atomic():
        cart = get_or_create_active_cart(user, branch_id=branch.id if branch else None)

        if cart.is_expired:
            raise CartExpired()

        # Branch consistency check
        if cart.branch_id and branch and str(cart.branch_id) != str(branch.id):
            raise BranchMismatch()

        # Resolve variant
        unit_price = product.base_price
        variant = None
        if variant_id:
            variant = ProductVariant.objects.filter(id=variant_id, product=product, is_active=True).first()
            if not variant:
                raise InvalidVariant()
            unit_price = variant.final_price

        # Validate and resolve modifiers
        resolved_modifiers = []
        if modifier_option_ids:
            resolved_modifiers = validate_modifier_selection(product, modifier_option_ids)
            unit_price += sum(opt.price_delta for opt in resolved_modifiers)

        # Merge with existing item (same product + variant + modifiers)
        existing = CartItem.objects.filter(
            cart=cart, product=product, variant=variant
        ).first()

        if existing and not modifier_option_ids:
            new_qty = existing.qty + qty
            if new_qty > MAX_CART_ITEM_QTY:
                raise InvalidQuantity(detail=f"Maximum {MAX_CART_ITEM_QTY} ta mahsulot qo'shish mumkin.")
            existing.qty = new_qty
            existing.unit_price = unit_price
            existing.save()
            cart_item = existing
        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                qty=qty,
                unit_price=unit_price,
                line_total=unit_price * qty,
                snapshot_name=product.name_ru,
                instructions=instructions,
            )
            for opt in resolved_modifiers:
                CartItemModifier.objects.create(
                    cart_item=cart_item,
                    modifier_option=opt,
                    price=opt.price_delta,
                    qty=1,
                )

        cart.recalculate()

    return cart_item


def update_cart_item(user, item_id, qty: int) -> CartItem:
    if qty < 1 or qty > MAX_CART_ITEM_QTY:
        raise InvalidQuantity()
    cart = get_active_cart(user)
    if not cart:
        raise CartNotFound()
    item = CartItem.objects.filter(id=item_id, cart=cart).first()
    if not item:
        raise CartItemNotFound()

    with transaction.atomic():
        item.qty = qty
        item.save()
        cart.recalculate()

    return item


def remove_cart_item(user, item_id) -> None:
    cart = get_active_cart(user)
    if not cart:
        raise CartNotFound()
    item = CartItem.objects.filter(id=item_id, cart=cart).first()
    if not item:
        raise CartItemNotFound()
    with transaction.atomic():
        item.delete()
        cart.recalculate()


def clear_cart(user) -> None:
    cart = get_active_cart(user)
    if not cart:
        raise CartNotFound()
    with transaction.atomic():
        cart.items.all().delete()
        cart.subtotal = 0
        cart.discount_amount = 0
        cart.delivery_fee = 0
        cart.service_fee = 0
        cart.total = 0
        cart.coupon_code = ""
        cart.save()


def apply_promo_code(user, code: str) -> Cart:
    """
    Apply a promo code to the active cart.
    Full promo validation is in the promotions app.
    Here we just attach the code; pricing service will validate at checkout.
    """
    from apps.carts.selectors import get_active_cart as _get

    cart = _get(user)
    if not cart:
        raise CartNotFound()
    if not cart.items.exists():
        raise CartEmpty()

    # Basic existence check — full validation at checkout
    from apps.promotions.selectors import get_active_promo  # noqa: deferred import
    promo = get_active_promo(code)
    if not promo:
        raise PromoCodeInvalid()
    if promo.min_order_amount and cart.subtotal < promo.min_order_amount:
        raise PromoMinOrderNotMet()

    cart.coupon_code = code.upper()
    cart.save(update_fields=["coupon_code", "updated_at"])
    return cart


def remove_promo_code(user) -> Cart:
    cart = get_active_cart(user)
    if not cart:
        raise CartNotFound()
    cart.coupon_code = ""
    cart.discount_amount = 0
    cart.recalculate()
    return cart
