from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsTicketOwnerOrOrganizationStaff(BasePermission):
    message = "You do not have permission to access this ticket."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        membership = OrganizationMembership.objects.filter(
            organization=obj.organization,
            user=user,
            is_active=True,
        ).first()

        if membership is None:
            return False

        if membership.role in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            return True

        if membership.role == OrganizationMembership.Role.CUSTOMER:
            return obj.customer_id == user.id

        return False