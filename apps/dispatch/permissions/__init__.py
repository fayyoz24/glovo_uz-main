from rest_framework.permissions import BasePermission


class IsDispatchAdmin(BasePermission):
    """Dispatch admin — faqat staff/superuser."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )
