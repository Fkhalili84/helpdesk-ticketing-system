from rest_framework.permissions import BasePermission

from .models import OrganizationMembership


class IsOrganizationMember(BasePermission):
    message = "You are not a member of this organization."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        organization = view.get_organization()

        if request.user.is_staff:
            return True

        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True,
        ).exists()


class IsOrganizationCustomer(BasePermission):
    message = "Only customers of this organization can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return False

        organization = view.get_organization()

        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        ).exists()


class IsOrganizationAgentOrAdmin(BasePermission):
    message = "Only organization agents or admins can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        organization = view.get_organization()

        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role__in=[
                OrganizationMembership.Role.AGENT,
                OrganizationMembership.Role.ADMIN,
            ],
            is_active=True,
        ).exists()