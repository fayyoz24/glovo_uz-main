from django.db import models


class AssignmentStatus(models.TextChoices):
    OFFERED = "offered", "Taklif qilindi"
    ACCEPTED = "accepted", "Qabul qilindi"
    REJECTED = "rejected", "Rad etildi"
    TIMED_OUT = "timed_out", "Vaqt tugadi"
    CANCELLED = "cancelled", "Bekor qilindi"
    COMPLETED = "completed", "Bajarildi"


# Kuryer taklifni qabul qilishi (yoki rad etishi) uchun berilgan vaqt (soniya).
# Uber/Bolt/Glovo kabi — kuryerga qisqa "ring" vaqti beriladi.
OFFER_TIMEOUT_SECONDS = 10

# Kuryer 10 soniya ichida javob bermasa yoki rad etsa, buyurtma "pending"
# (kuryer kutilmoqda) holatiga o'tadi va shuncha soniyadan keyin navbatdagi
# eng yaqin kuryerga qayta taklif yuboriladi.
PENDING_RETRY_SECONDS = 300  # 5 daqiqa

# Nechta marta qayta urinishdan keyin admin/ops qatoriga eskalatsiya qilinadi
MAX_ASSIGNMENT_ATTEMPTS = 5

# Oxirgi ping qanchalik yangi bo'lishi kerak (daqiqa) — shundan eski
# joylashuvga ega kuryerlar qidiruvga kiritilmaydi
MAX_PING_AGE_MINUTES = 5

# Radius bo'yicha filtr endi qo'llanilmaydi — har doim ENG YAQIN mavjud
# kuryer tanlanadi. Bu faqat mutlaqo mantiqsiz (masalan, boshqa
# viloyatdagi) kuryerlarni chetlab o'tish uchun xavfsizlik cheki.
MAX_SEARCH_RADIUS_KM = 50.0
