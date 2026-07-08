from rest_framework.permissions import BasePermission


class IsMerchantStaff(BasePermission):
    """Foydalanuvchi merchant xodimi (owner/manager) ekanligini tekshiradi."""
    message = "Bu amalni bajarish uchun merchant xodimi bo'lishingiz kerak."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "merchant_staff_profile")
            and request.user.merchant_staff_profile is not None
        )


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
