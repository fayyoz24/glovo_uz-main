from rest_framework.permissions import BasePermission


class IsNotificationOwner(BasePermission):
    """
    Only the recipient can read/mark their own notifications.
    Used on detail endpoints if needed.
    """

    def has_object_permission(self, request, view, obj):
        return obj.recipient_id == request.user.pk
