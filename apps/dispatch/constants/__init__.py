from django.db import models


class AssignmentStatus(models.TextChoices):
    OFFERED = "offered", "Taklif qilindi"
    ACCEPTED = "accepted", "Qabul qilindi"
    REJECTED = "rejected", "Rad etildi"
    TIMED_OUT = "timed_out", "Vaqt tugadi"
    CANCELLED = "cancelled", "Bekor qilindi"
    COMPLETED = "completed", "Bajarildi"


# Kuryer taklifni qabul qilishi uchun berilgan vaqt (soniya)
OFFER_TIMEOUT_SECONDS = 30

# Takroriy tayinlash uchun maksimal urinishlar
MAX_ASSIGNMENT_ATTEMPTS = 5

# Radiusi (km) — filialdan kuryerlarga
DEFAULT_SEARCH_RADIUS_KM = 3.0

# Oxirgi ping qanchalik yangi bo'lishi kerak (daqiqa)
MAX_PING_AGE_MINUTES = 5
