import uuid
from django.db import models
from django.utils import timezone
# from apps.carts.constants import CartStatus, CART_EXPIRY_HOURS
from apps.carts.constants import MAX_CART_ITEM_QTY, CART_EXPIRY_HOURS, CartStatus

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="carts",
    )
    branch = models.ForeignKey(
        "merchants.MerchantBranch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="carts",
    )
    status = models.CharField(
        max_length=20,
        choices=CartStatus.choices,
        default=CartStatus.ACTIVE,
    )
    coupon_code = models.CharField(max_length=50, blank=True)
    # All monetary values in tiyin (UZS smallest unit)
    subtotal = models.PositiveIntegerField(default=0)
    discount_amount = models.PositiveIntegerField(default=0)
    delivery_fee = models.PositiveIntegerField(default=0)
    service_fee = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts_cart"
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Cart({self.user.phone}, {self.status})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=CART_EXPIRY_HOURS)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def recalculate(self):
        """Recalculate subtotal and total from items."""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total = self.subtotal + self.delivery_fee + self.service_fee - self.discount_amount
        self.save(update_fields=["subtotal", "total", "updated_at"])


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="+",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    qty = models.PositiveSmallIntegerField(default=1)
    unit_price = models.PositiveIntegerField(help_text="Price at time of adding to cart, in tiyin")
    line_total = models.PositiveIntegerField()
    snapshot_name = models.CharField(max_length=200, blank=True, help_text="Product name snapshot")
    instructions = models.TextField(blank=True, help_text="Special instructions from customer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts_cart_item"

    def __str__(self):
        return f"{self.snapshot_name or self.product.name_ru} x{self.qty}"

    def save(self, *args, **kwargs):
        # Auto-snapshot product name and calculate line_total
        if not self.snapshot_name:
            self.snapshot_name = self.product.name_ru
        self.line_total = self.unit_price * self.qty
        super().save(*args, **kwargs)


class CartItemModifier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart_item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        related_name="modifiers",
    )
    modifier_option = models.ForeignKey(
        "catalog.ProductModifierOption",
        on_delete=models.CASCADE,
        related_name="+",
    )
    price = models.PositiveIntegerField(help_text="Price delta at time of selection, in tiyin")
    qty = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "carts_cart_item_modifier"

    def __str__(self):
        return f"{self.cart_item} + {self.modifier_option.name_ru}"
