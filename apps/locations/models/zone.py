import uuid
from django.db import models
from apps.locations.constants import City


class ServiceZone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=50, choices=City.CHOICES, default=City.DEFAULT)
    # For MVP: circle-based zone (lat/lng center + radius)
    center_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    center_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # For future: polygon geometry via PostGIS
    # geometry = models.PolygonField(null=True, blank=True)
    delivery_fee_override = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Override delivery fee in UZS smallest unit for this zone",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "locations_service_zone"

    def __str__(self):
        return f"{self.name} ({self.city})"
