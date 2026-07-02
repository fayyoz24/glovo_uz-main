from rest_framework.permissions import BasePermission


class IsAdminAnalytics(BasePermission):
    message = "You do not have permission to access analytics."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        role = getattr(user, "role", None)
        return role in {"admin", "ops", "support", "finance"}
