from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers import CustomerRegisterSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from .models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
)

from .permissions import IsOrganizationAdmin

from .serializers import (
    InvitationAcceptSerializer,
    OrganizationInvitationSerializer,
    OrganizationOnboardingSerializer,
)


class OrganizationOnboardingView(
    generics.CreateAPIView,
):
    serializer_class = OrganizationOnboardingSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        result = serializer.save()

        user = result["user"]
        organization = result["organization"]

        return Response(
            {
                "message": "Organization created successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "organization": {
                    "id": organization.id,
                    "name": organization.name,
                    "slug": organization.slug,
                },
                "role": OrganizationMembership.Role.ADMIN,
            },
            status=status.HTTP_201_CREATED,
        )

class OrganizationMixin:
    def get_organization(self):
        if not hasattr(self, "_organization"):
            self._organization = get_object_or_404(
                Organization,
                slug=self.kwargs["organization_slug"],
                is_active=True,
            )

        return self._organization
    
class OrganizationInvitationListCreateView(
    OrganizationMixin,
    generics.ListCreateAPIView,
):
    serializer_class = OrganizationInvitationSerializer

    permission_classes = [
        IsAuthenticated,
        IsOrganizationAdmin,
    ]

    def get_queryset(self):
        return OrganizationInvitation.objects.filter(
            organization=self.get_organization(),
        ).select_related(
            "organization",
            "invited_by",
        ).order_by(
            "-created_at",
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["organization"] = self.get_organization()

        return context

    def perform_create(self, serializer):
        serializer.save(
            organization=self.get_organization(),
            invited_by=self.request.user,
            role=OrganizationMembership.Role.AGENT,
            expires_at=(
                timezone.now()
                + timedelta(days=7)
            ),
        )


class InvitationDetailView(
    generics.RetrieveAPIView,
):
    serializer_class = OrganizationInvitationSerializer

    permission_classes = [
        AllowAny,
    ]

    queryset = OrganizationInvitation.objects.select_related(
        "organization",
        "invited_by",
    )

    lookup_field = "token"
    lookup_url_kwarg = "token"


class InvitationAcceptView(APIView):
    permission_classes = [
        AllowAny,
    ]
    @extend_schema(
        tags=["Organizations"],
        summary="Accept organization invitation",
        description=(
            "Accepts a valid organization invitation "
            "for the authenticated user."
        ),
        request=None,
        responses={
            200: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request, token):
        invitation = get_object_or_404(
            OrganizationInvitation.objects.select_related(
                "organization",
            ),
            token=token,
        )

        serializer = InvitationAcceptSerializer(
            data=request.data,
            context={
                "invitation": invitation,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.save()

        return Response(
            {
                "message": "Invitation accepted successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "organization": {
                    "id": invitation.organization.id,
                    "name": invitation.organization.name,
                    "slug": invitation.organization.slug,
                },
                "role": OrganizationMembership.Role.AGENT,
            },
            status=status.HTTP_201_CREATED,
        )
    

class CustomerRegisterView(
    OrganizationMixin,
    generics.CreateAPIView,
):
    serializer_class = CustomerRegisterSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["organization"] = self.get_organization()

        return context