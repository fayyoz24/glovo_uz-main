from rest_framework.permissions import BasePermission


class IsMerchantStaff(BasePermission):
    """Foydalanuvchi merchant staff ekanligini tekshiradi."""
    message = "Bu amalni bajarish uchun merchant xodimi bo'lishingiz kerak."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "merchant_staff_profile")
            and request.user.merchant_staff_profile is not None
        )


class IsOrderOwner(BasePermission):
    """Buyurtma foydalanuvchiga tegishli ekanligini tekshiradi."""
    message = "Bu buyurtma sizga tegishli emas."

    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user
