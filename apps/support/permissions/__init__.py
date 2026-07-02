from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Allow access only to users with role='customer'."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "customer"
        )


class IsSupportAgent(BasePermission):
    """Allow access only to staff/admin users acting as support agents."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or getattr(request.user, "role", None) in ("admin", "support"))
        )


class IsComplaintOwnerOrSupport(BasePermission):
    """
    Object-level permission:
    - The customer who created the complaint can access it.
    - Support agents can access any complaint.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or getattr(user, "role", None) in ("admin", "support"):
            return True
        # obj is a Complaint
        return str(obj.customer_id) == str(user.id)


class IsRefundRequestOwnerOrSupport(BasePermission):
    """
    Object-level permission for RefundRequest.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or getattr(user, "role", None) in ("admin", "support"):
            return True
        return str(obj.customer_id) == str(user.id)
