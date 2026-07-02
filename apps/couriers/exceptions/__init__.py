from rest_framework.exceptions import APIException
from rest_framework import status


class CourierProfileNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Kuryer profili topilmadi."
    default_code = "courier_profile_not_found"


class CourierAlreadyOnline(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Kuryer allaqachon onlayn."
    default_code = "courier_already_online"


class CourierAlreadyOffline(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Kuryer allaqachon oflayn."
    default_code = "courier_already_offline"


class CourierNotOnline(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Buyurtmani qabul qilish uchun onlayn bo'lishingiz kerak."
    default_code = "courier_not_online"


class ActiveShiftExists(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Faol smena allaqachon mavjud."
    default_code = "active_shift_exists"
