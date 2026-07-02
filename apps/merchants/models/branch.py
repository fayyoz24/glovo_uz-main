import uuid
from django.db import models
from apps.common.constants import Weekday


class MerchantBranch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        related_name="branches",
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address_text = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    service_radius_km = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    prep_time_min = models.PositiveSmallIntegerField(default=20, help_text="Average preparation time in minutes")
    is_open = models.BooleanField(default=False)
    accepting_orders = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchants_branch"
        indexes = [
            models.Index(fields=["merchant", "is_open", "accepting_orders"]),
        ]

    def __str__(self):
        return f"{self.merchant.name} – {self.name}"


class BranchWorkingHour(models.Model):
    id = models.AutoField(primary_key=True)
    branch = models.ForeignKey(
        MerchantBranch,
        on_delete=models.CASCADE,
        related_name="working_hours",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.CHOICES)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False, help_text="Closed all day on this weekday")

    class Meta:
        db_table = "merchants_branch_working_hour"
        unique_together = [("branch", "weekday")]

    def __str__(self):
        day = dict(Weekday.CHOICES).get(self.weekday, self.weekday)
        if self.is_closed:
            return f"{self.branch} – {day}: CLOSED"
        return f"{self.branch} – {day}: {self.open_time}–{self.close_time}"
