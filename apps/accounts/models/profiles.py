import uuid
from django.db import models
from apps.accounts.constants import VehicleType
from apps.couriers.constants import CourierStatus

class CustomerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_customer_profile"

    def __str__(self):
        return f"CustomerProfile({self.user.phone})"


class CourierProfile(models.Model): 
    user = models.OneToOneField( "accounts.User", on_delete=models.CASCADE, related_name="courier_profile", ) 
    vehicle_type = models.CharField( max_length=20, choices=VehicleType.CHOICES, default=VehicleType.MOTORBIKE, ) 
    vehicle_number = models.CharField(max_length=20, blank=True) 
    passport_number = models.CharField(max_length=20, blank=True) 
    photo = models.ImageField(upload_to="couriers/photos/", null=True, blank=True) # Holat 
    courier_status = models.CharField( max_length=20, choices=CourierStatus.choices, default=CourierStatus.OFFLINE, ) 
    is_approved = models.BooleanField(default=False) # Joylashuv (oxirgi ping) 
    current_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True) 
    current_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True) 
    last_location_at = models.DateTimeField(null=True, blank=True) # Rating 
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00) 
    total_deliveries = models.PositiveIntegerField(default=0) # Moliya 
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0) 
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta: 
        db_table = "accounts_courier_profile" 

    def __str__(self): 
        return f"Courier: {self.user}"
        
    @property 
    def is_online(self): 
        return self.courier_status in ( CourierStatus.ONLINE, CourierStatus.BUSY ) 

    @property 
    def is_available(self): 
        return self.courier_status == CourierStatus.ONLINE