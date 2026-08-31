from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Organization,
    OrganizationMembership,
)

from .organization_serializers import (
    OrganizationDetailSerializer,
    OrganizationUpdateSerializer,
)


class OrganizationAccessMixin:
    permission_classes = [
        IsAuthenticated,
    ]

    def get_organization(self):
        if not hasattr(
            self,
            "_organization",
        ):
            self._organization = (
                get_object_or_404(
                    Organization,
                    slug=self.kwargs[
                        "organization_slug"
                    ],
                    is_active=True,
                )
            )

        return self._organization

    def get_membership(self):
        organization = (
            self.get_organization()
        )

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=self.request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not an active member "
                "of this organization."
            )

        return membership

    def require_admin(self):
        membership = (
            self.get_membership()
        )

        if (
            membership.role
            != OrganizationMembership.Role.ADMIN
        ):
            raise PermissionDenied(
                "Only an active organization admin "
                "can update organization settings."
            )

        return membership


class OrganizationDetailView(
    OrganizationAccessMixin,
    APIView,
):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Organizations"],
        summary="Get organization details",
        description=(
            "Returns organization information and "
            "organization statistics. The authenticated "
            "user must be an active member."
        ),
        responses={
            200: OrganizationDetailSerializer,
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        self.get_membership()

        organization = (
            self.get_organization()
        )

        serializer = (
            OrganizationDetailSerializer(
                organization
            )
        )

        return Response(
            serializer.data
        )

    @extend_schema(
        tags=["Organizations"],
        summary="Update organization",
        description=(
            "Updates organization settings. "
            "Only active organization admins can "
            "perform this operation."
        ),
        request=OrganizationUpdateSerializer,
        responses={
            200: OrganizationDetailSerializer,
        },
    )
    def patch(
        self,
        request,
        organization_slug,
    ):
        self.require_admin()

        organization = (
            self.get_organization()
        )

        with transaction.atomic():
            locked_organization = (
                Organization.objects
                .select_for_update()
                .get(
                    pk=organization.pk,
                )
            )

            serializer = (
                OrganizationUpdateSerializer(
                    locked_organization,
                    data=request.data,
                    partial=True,
                )
            )

            serializer.is_valid(
                raise_exception=True
            )

            serializer.save()

            response_serializer = (
                OrganizationDetailSerializer(
                    locked_organization
                )
            )

            response_data = (
                response_serializer.data
            )

        return Response(
            response_data
        )