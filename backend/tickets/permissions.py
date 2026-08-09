from rest_framework.permissions import BasePermission

from users.models import User


class IsTicketOwnerOrAgent(BasePermission):
    message = "You do not have permission to access this ticket."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        if user.role == User.Role.AGENT:
            return True

        return obj.customer_id == user.id