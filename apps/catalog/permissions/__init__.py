from rest_framework.permissions import BasePermission
from apps.accounts.constants import UserRole


class IsMerchantOwnerOrManager(BasePermission):
    """Merchant staff can manage their own products."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_merchant_staff
        )

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, "merchant_staff_profile"):
            return False
        return request.user.merchant_staff_profile.merchant_id == obj.merchant_id
