from rest_framework.permissions import BasePermission

from .models import User


class IsCustomer(BasePermission):
    message = "Only customers can perform this action."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.role == User.Role.CUSTOMER
            and not user.is_staff
        )


class IsAgentOrAdmin(BasePermission):
    message = "Only support agents or administrators can perform this action."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and (
                user.role == User.Role.AGENT
                or user.is_staff
            )
        )