import uuid
from django.db import models
from apps.couriers.constants import ShiftStatus


class CourierShift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    courier = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="shifts",
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ShiftStatus.choices,
        default=ShiftStatus.ACTIVE,
    )
    # Smena davomida amalga oshirilgan yetkazib berishlar
    deliveries_count = models.PositiveIntegerField(default=0)
    total_earned = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "courier_shift"
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["courier", "status"]),
        ]

    def __str__(self):
        return f"Shift {self.courier} – {self.status}"

    @property
    def duration_minutes(self):
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
