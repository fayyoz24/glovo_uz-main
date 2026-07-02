import uuid
from django.db import models
from apps.dispatch.constants import AssignmentStatus


class CourierAssignment(models.Model):
    """
    Har bir order uchun kuryer tayinlash yozuvi.
    Bir order uchun bir nechta yozuv bo'lishi mumkin
    (rad etilsa yoki vaqt tugasa yangi yozuv yaratiladi).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    courier = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="courier_assignments",
    )
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.OFFERED,
    )
    # Urinish raqami (1-dan boshlanganda)
    attempt_number = models.PositiveIntegerField(default=1)
    # Taklifni qabul qilish muddati
    offer_expires_at = models.DateTimeField()

    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Taxminiy masofa (km)
    distance_km = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "courier_assignment"
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["courier", "status"]),
            models.Index(fields=["offer_expires_at"]),
        ]

    def __str__(self):
        return f"Assignment order={self.order.public_id} courier={self.courier} [{self.status}]"

    @property
    def is_active(self):
        return self.status == AssignmentStatus.OFFERED

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.is_active and timezone.now() > self.offer_expires_at
