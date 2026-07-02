import uuid
from django.db import models


class CourierLocationPing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    courier = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="location_pings",
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    accuracy = models.FloatField(null=True, blank=True, help_text="GPS aniqlik (metr)")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "courier_location_ping"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["courier", "recorded_at"]),
        ]
        # Eski yozuvlarni avtomatik tozalash uchun partitioning Phase 2 da
        # qo'shiladi (recorded_at bo'yicha)

    def __str__(self):
        return f"{self.courier} @ ({self.latitude}, {self.longitude})"
