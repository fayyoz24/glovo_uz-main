from rest_framework.exceptions import APIException
from rest_framework import status


class AssignmentNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tayinlash topilmadi."
    default_code = "assignment_not_found"


class AssignmentAlreadyActioned(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bu tayinlash allaqachon qabul qilingan yoki rad etilgan."
    default_code = "assignment_already_actioned"


class NoCouriersAvailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Hozirda mavjud kuryer topilmadi. Admin xabardor qilindi."
    default_code = "no_couriers_available"


class MaxAttemptsReached(Exception):
    """Dispatch urinishlari limitiga yetildi — admin escalation."""
    pass
