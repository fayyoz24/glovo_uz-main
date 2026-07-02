import uuid
from django.db import models


class DeviceToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="account_device_tokens",
    )
    token = models.TextField()
    platform = models.CharField(
        max_length=10,
        choices=[("ios", "iOS"), ("android", "Android"), ("web", "Web")],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_device_token"
        unique_together = [("user", "token")]

    def __str__(self):
        return f"Device({self.user.phone}, {self.platform})"