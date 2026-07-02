from django.db import models


class VehicleType(models.TextChoices):
    BICYCLE = "bicycle", "Velosiped"
    MOTORCYCLE = "motorcycle", "Mototsikl"
    CAR = "car", "Avtomobil"
    FOOT = "foot", "Piyoda"


class ShiftStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    ENDED = "ended", "Tugagan"


class CourierStatus(models.TextChoices):
    OFFLINE = "offline", "Oflayn"
    ONLINE = "online", "Onlayn"
    BUSY = "busy", "Band"
