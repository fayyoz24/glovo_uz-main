from rest_framework.permissions import BasePermission


class IsAdminOrOps(BasePermission):
    """Admin yoki ops rolida bo'lgan foydalanuvchi."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "ops", "support")
        )


class IsPromoOwnerOrAdmin(BasePermission):
    """Faqat admin yoki ownerni ruxsat beradi."""

    def has_object_permission(self, request, view, obj):
        if request.user.role in ("admin", "ops"):
            return True
        return False
