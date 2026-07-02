from rest_framework.permissions import BasePermission


class IsMerchantOwner(BasePermission):
    """Allows access only to the owner of the merchant being accessed."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsBranchStaff(BasePermission):
    """Allows merchant staff to access their own branch."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not hasattr(user, "merchant_staff_profile"):
            return False
        profile = user.merchant_staff_profile
        return profile.merchant_id == obj.merchant_id
