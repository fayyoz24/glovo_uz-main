from rest_framework.exceptions import APIException
from rest_framework import status


class OrderNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Buyurtma topilmadi."
    default_code = "order_not_found"


class InvalidOrderTransition(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bu holat o'tishi ruxsat etilmagan."
    default_code = "invalid_order_transition"


class OrderNotCancellable(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bu buyurtmani bekor qilib bo'lmaydi."
    default_code = "order_not_cancellable"


class EmptyCartError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Savat bo'sh. Buyurtma berish uchun avval mahsulot qo'shing."
    default_code = "empty_cart"


class BranchClosedError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Filial hozir yopiq yoki buyurtma qabul qilmayapti."
    default_code = "branch_closed"


class CheckoutError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Checkout jarayonida xatolik yuz berdi."
    default_code = "checkout_error"
