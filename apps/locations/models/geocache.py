import uuid
from django.db import models


class GeocodingCache(models.Model):
    """Cache geocoding results to minimize external API calls."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.CharField(max_length=500, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    formatted_address = models.TextField(blank=True)
    provider = models.CharField(
        max_length=20,
        choices=[("yandex", "Yandex"), ("google", "Google"), ("2gis", "2GIS")],
        default="yandex",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "locations_geocoding_cache"
        indexes = [
            models.Index(fields=["query"]),
        ]

    def __str__(self):
        return f"Geocache({self.query[:50]})"
