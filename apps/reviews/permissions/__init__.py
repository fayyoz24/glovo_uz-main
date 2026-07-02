from rest_framework.permissions import BasePermission


class IsAdminOrOps(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "ops", "support")
        )


class IsMerchantStaff(BasePermission):
    """Merchant panel'da ishlayotgan foydalanuvchi."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("merchant_owner", "merchant_manager")
        )


class IsReviewOwner(BasePermission):
    """Faqat review egasi o'zgartira oladi."""

    def has_object_permission(self, request, view, obj):
        return obj.customer_id == request.user.id
