from django.db import transaction
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import (
    DjangoFilterBackend,
)

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .member_serializers import (
    OrganizationMemberSerializer,
    OrganizationMemberUpdateSerializer,
)

from .member_services import (
    ensure_admin_continuity,
    unassign_member_tickets,
)

from .models import (
    Organization,
    OrganizationMembership,
)


class OrganizationAdminAccessMixin:
    permission_classes = [
        IsAuthenticated,
    ]

    def get_organization(self):
        if not hasattr(
            self,
            "_member_management_organization",
        ):
            self._member_management_organization = (
                get_object_or_404(
                    Organization,
                    slug=self.kwargs[
                        "organization_slug"
                    ],
                    is_active=True,
                )
            )

        return self._member_management_organization

    def require_organization_admin(self):
        organization = self.get_organization()

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=self.request.user,
                role=OrganizationMembership.Role.ADMIN,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "Only an active organization admin "
                "can manage organization members."
            )

        return membership

    def get_target_membership(
        self,
        *,
        lock=False,
    ):
        organization = self.get_organization()

        queryset = (
            OrganizationMembership.objects
            .select_related(
                "user",
                "organization",
            )
            .filter(
                organization=organization,
            )
        )

        if lock:
            queryset = queryset.select_for_update()

        return get_object_or_404(
            queryset,
            pk=self.kwargs["membership_id"],
        )


class OrganizationMemberListView(
    OrganizationAdminAccessMixin,
    generics.ListAPIView,
):
    serializer_class = OrganizationMemberSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]

    filterset_fields = [
        "role",
        "is_active",
    ]

    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    def get_queryset(self):
        self.require_organization_admin()

        organization = self.get_organization()

        return (
            OrganizationMembership.objects
            .filter(
                organization=organization,
            )
            .select_related(
                "user",
                "organization",
            )
            .order_by(
                "user__username",
            )
        )


class OrganizationMemberDetailView(
    OrganizationAdminAccessMixin,
    APIView,
):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        organization_slug,
        membership_id,
    ):
        self.require_organization_admin()

        membership = self.get_target_membership()

        serializer = OrganizationMemberSerializer(
            membership
        )

        return Response(
            serializer.data
        )

    def patch(
        self,
        request,
        organization_slug,
        membership_id,
    ):
        self.require_organization_admin()

        organization = self.get_organization()

        with transaction.atomic():
            membership = self.get_target_membership(
                lock=True,
            )

            serializer = (
                OrganizationMemberUpdateSerializer(
                    membership,
                    data=request.data,
                    partial=True,
                )
            )

            serializer.is_valid(
                raise_exception=True
            )

            final_role = (
                serializer.validated_data.get(
                    "role",
                    membership.role,
                )
            )

            final_is_active = (
                serializer.validated_data.get(
                    "is_active",
                    membership.is_active,
                )
            )

            ensure_admin_continuity(
                membership=membership,
                final_role=final_role,
                final_is_active=final_is_active,
            )

            membership = serializer.save()

            should_unassign_tickets = (
                not membership.is_active
                or membership.role
                == OrganizationMembership.Role.CUSTOMER
            )

            if should_unassign_tickets:
                unassign_member_tickets(
                    organization=organization,
                    user=membership.user,
                    changed_by=request.user,
                )

            response_serializer = (
                OrganizationMemberSerializer(
                    membership
                )
            )

            response_data = (
                response_serializer.data
            )

        return Response(
            response_data
        )

    def delete(
        self,
        request,
        organization_slug,
        membership_id,
    ):
        self.require_organization_admin()

        organization = self.get_organization()

        with transaction.atomic():
            membership = self.get_target_membership(
                lock=True,
            )

            ensure_admin_continuity(
                membership=membership,
                final_role=membership.role,
                final_is_active=False,
            )

            unassign_member_tickets(
                organization=organization,
                user=membership.user,
                changed_by=request.user,
            )

            membership.delete()

        return Response(
            status=204
        )