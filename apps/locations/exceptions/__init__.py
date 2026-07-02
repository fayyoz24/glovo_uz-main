from rest_framework.exceptions import APIException
from rest_framework import status


class AddressNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Address not found."
    default_code = "address_not_found"


class AddressLimitExceeded(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You have reached the maximum number of saved addresses."
    default_code = "address_limit_exceeded"


class OutsideServiceZone(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This address is outside our current service zone."
    default_code = "outside_service_zone"
