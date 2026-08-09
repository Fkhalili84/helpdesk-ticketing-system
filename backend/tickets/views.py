from django.shortcuts import get_object_or_404

from rest_framework import generics, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from users.models import User
from users.permissions import IsCustomer

from .models import Ticket, TicketCategory, TicketMessage
from .permissions import IsTicketOwnerOrAgent
from .serializers import (
    TicketCategorySerializer,
    TicketMessageSerializer,
    TicketSerializer,
)

class TicketCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TicketCategory.objects.all().order_by("name")
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAuthenticated]


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Ticket.objects.select_related(
            "customer",
            "assigned_agent",
            "category",
        )

        if user.is_staff or user.role == User.Role.AGENT:
            return queryset

        return queryset.filter(customer=user)

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [
                IsAuthenticated,
                IsCustomer,
            ]

        elif self.action == "destroy":
            permission_classes = [
                IsAdminUser,
            ]

        else:
            permission_classes = [
                IsAuthenticated,
                IsTicketOwnerOrAgent,
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def perform_create(self, serializer):
        serializer.save(
            customer=self.request.user,
        )


class TicketMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketMessageSerializer
    permission_classes = [
        IsAuthenticated,
        IsTicketOwnerOrAgent,
    ]

    def get_ticket(self):
        if not hasattr(self, "_ticket"):
            ticket = get_object_or_404(
                Ticket.objects.select_related("customer"),
                pk=self.kwargs["ticket_id"],
            )

            self.check_object_permissions(
                self.request,
                ticket,
            )

            self._ticket = ticket

        return self._ticket

    def get_queryset(self):
        ticket = self.get_ticket()

        return TicketMessage.objects.filter(
            ticket=ticket,
        ).select_related("sender")

    def perform_create(self, serializer):
        serializer.save(
            ticket=self.get_ticket(),
            sender=self.request.user,
        )