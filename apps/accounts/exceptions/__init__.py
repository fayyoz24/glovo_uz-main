from rest_framework.exceptions import APIException
from rest_framework import status


class LoginCodeExpired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Kod muddati tugagan. Botdan yangi kod oling."
    default_code = "login_code_expired"


class LoginCodeInvalid(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Kod noto'g'ri."
    default_code = "login_code_invalid"


class LoginCodeMaxAttemptsReached(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Urinishlar soni tugadi. Botdan yangi kod oling."
    default_code = "login_code_max_attempts"


class LoginCodeCooldownActive(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Iltimos, yangi kod so'rashdan oldin biroz kuting."
    default_code = "login_code_cooldown"


class UserInactive(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "User account is disabled."
    default_code = "user_inactive"
