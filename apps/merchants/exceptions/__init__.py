from rest_framework.exceptions import APIException
from rest_framework import status


class MerchantNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Merchant not found."
    default_code = "merchant_not_found"


class BranchNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Branch not found."
    default_code = "branch_not_found"


class MerchantNotActive(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This merchant is not currently active."
    default_code = "merchant_not_active"


class BranchNotAcceptingOrders(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This branch is not currently accepting orders."
    default_code = "branch_not_accepting"
