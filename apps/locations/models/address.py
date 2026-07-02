import uuid
from django.db import models
from apps.locations.constants import City


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    title = models.CharField(max_length=100, blank=True, help_text="Home, Work, etc.")
    address_line = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, help_text="Near landmark for local delivery")
    entrance = models.CharField(max_length=20, blank=True)
    floor = models.CharField(max_length=10, blank=True)
    apartment = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, choices=City.CHOICES, default=City.DEFAULT)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "locations_address"
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self):
        return f"{self.title or 'Address'} – {self.address_line}"

    def save(self, *args, **kwargs):
        # Ensure only one default per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
