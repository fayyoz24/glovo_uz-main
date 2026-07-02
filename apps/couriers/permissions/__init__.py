from rest_framework.permissions import BasePermission


class IsCourier(BasePermission):
    """Foydalanuvchi tasdiqlangan kuryer ekanligini tekshiradi."""
    message = "Bu amalni bajarish uchun kuryer bo'lishingiz kerak."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.courier_profile is not None
        except Exception:
            return False


class IsApprovedCourier(BasePermission):
    """Tasdiqlangan kuryer."""
    message = "Hisobingiz hali tasdiqlanmagan."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.courier_profile.is_approved
        except Exception:
            return False
