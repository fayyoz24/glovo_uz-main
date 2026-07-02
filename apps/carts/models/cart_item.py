import uuid
from django.db import models


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        "carts.Cart",
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    snapshot_name = models.CharField(max_length=255, blank=True)
    instructions = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_item"

    def __str__(self):
        return f"{self.snapshot_name or self.product.name_uz} x{self.qty}"

    def save(self, *args, **kwargs):
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
    price = models.DecimalField(max_digits=12, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_item_modifier"

    def __str__(self):
        return f"{self.modifier_option.name_uz} x{self.qty}"
