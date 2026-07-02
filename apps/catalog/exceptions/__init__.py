from rest_framework.exceptions import APIException
from rest_framework import status


class ProductNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Product not found."
    default_code = "product_not_found"


class ProductNotAvailable(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This product is currently unavailable."
    default_code = "product_not_available"


class CategoryNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Category not found."
    default_code = "category_not_found"


class InvalidVariant(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid product variant selected."
    default_code = "invalid_variant"


class InvalidModifier(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid modifier option selected."
    default_code = "invalid_modifier"


class ModifierSelectionError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Modifier selection does not meet the required min/max constraints."
    default_code = "modifier_selection_error"
