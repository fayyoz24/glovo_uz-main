from rest_framework.exceptions import APIException
from rest_framework import status


class CartNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Active cart not found."
    default_code = "cart_not_found"


class CartExpired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Your cart has expired. Please start a new cart."
    default_code = "cart_expired"


class CartItemNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Cart item not found."
    default_code = "cart_item_not_found"


class BranchMismatch(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You already have items from a different branch. Please clear your cart first."
    default_code = "branch_mismatch"


class CartBranchConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Your cart already contains items from another branch. "
        "Please clear your cart before adding products from a different branch."
    )
    default_code = "cart_branch_conflict"


class InvalidQuantity(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid quantity."
    default_code = "invalid_quantity"


class InvalidPromoCode(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Promo code is invalid or has expired."
    default_code = "promo_invalid"


class PromoMinOrderNotMet(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Minimum order amount not met for this promo code."
    default_code = "promo_min_order"


class CartEmpty(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Your cart is empty."
    default_code = "cart_empty"
