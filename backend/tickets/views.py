from django.shortcuts import get_object_or_404

from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from organizations.models import (
    Organization,
    OrganizationMembership,
)
from organizations.permissions import (
    IsOrganizationAdmin,
    IsOrganizationCustomer,
    IsOrganizationMember,
)

from .models import (
    Ticket,
    TicketCategory,
    TicketMessage,
)
from .permissions import IsTicketOwnerOrOrganizationStaff
from .serializers import (
    TicketCategorySerializer,
    TicketMessageSerializer,
    TicketSerializer,
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

    def get_membership(self):
        if self.request.user.is_staff:
            return None

        return OrganizationMembership.objects.filter(
            organization=self.get_organization(),
            user=self.request.user,
            is_active=True,
        ).first()


class TicketCategoryViewSet(
    OrganizationMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = TicketCategorySerializer
    permission_classes = [
        IsAuthenticated,
        IsOrganizationMember,
    ]

    def get_queryset(self):
        return TicketCategory.objects.filter(
            organization=self.get_organization(),
        ).order_by("name")


class TicketViewSet(
    OrganizationMixin,
    viewsets.ModelViewSet,
):
    serializer_class = TicketSerializer

    def get_queryset(self):
        organization = self.get_organization()

        queryset = Ticket.objects.filter(
            organization=organization,
        ).select_related(
            "organization",
            "customer",
            "assigned_agent",
            "category",
        )

        user = self.request.user

        if user.is_staff:
            return queryset

        membership = self.get_membership()

        if membership is None:
            return queryset.none()

        if membership.role in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            return queryset

        return queryset.filter(
            customer=user,
        )

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [
                IsAuthenticated,
                IsOrganizationCustomer,
            ]
    
        elif self.action == "destroy":
            permission_classes = [
                IsAuthenticated,
                IsOrganizationAdmin,
            ]
    
        else:
            permission_classes = [
                IsAuthenticated,
                IsOrganizationMember,
                IsTicketOwnerOrOrganizationStaff,
            ]
    
        return [
            permission()
            for permission in permission_classes
        ]

    def perform_create(self, serializer):
        serializer.save(
            organization=self.get_organization(),
            customer=self.request.user,
        )


class TicketMessageListCreateView(
    OrganizationMixin,
    generics.ListCreateAPIView,
):
    serializer_class = TicketMessageSerializer

    permission_classes = [
        IsAuthenticated,
        IsOrganizationMember,
        IsTicketOwnerOrOrganizationStaff,
    ]

    def get_ticket(self):
        if not hasattr(self, "_ticket"):
            ticket = get_object_or_404(
                Ticket.objects.select_related(
                    "organization",
                    "customer",
                ),
                pk=self.kwargs["ticket_id"],
                organization=self.get_organization(),
            )

            self.check_object_permissions(
                self.request,
                ticket,
            )

            self._ticket = ticket

        return self._ticket

    def get_queryset(self):
        return TicketMessage.objects.filter(
            ticket=self.get_ticket(),
        ).select_related(
            "sender",
        )

    def perform_create(self, serializer):
        serializer.save(
            ticket=self.get_ticket(),
            sender=self.request.user,
        )