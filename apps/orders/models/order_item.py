import uuid
from django.db import models


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product_id = models.UUIDField()
    product_name_snapshot = models.CharField(max_length=255)
    variant_snapshot = models.CharField(max_length=128, blank=True)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    instructions = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = "order_item"

    def __str__(self):
        return f"{self.product_name_snapshot} x{self.qty}"


class OrderItemModifier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="modifiers",
    )
    modifier_name = models.CharField(max_length=128)
    modifier_price = models.DecimalField(max_digits=12, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "order_item_modifier"
