from apps.carts.models import Cart
from apps.carts.constants import CartStatus


def get_active_cart(user) -> Cart | None:
    """Return user's current active cart with all items prefetched."""
    return (
        Cart.objects.filter(user=user, status=CartStatus.ACTIVE)
        .prefetch_related(
            "items__product__images",
            "items__variant",
            "items__modifiers__modifier_option",
        )
        .select_related("branch__merchant")
        .order_by("-created_at")
        .first()
    )


def get_cart_by_id(cart_id, user) -> Cart | None:
    return Cart.objects.filter(id=cart_id, user=user).first()
