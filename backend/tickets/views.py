from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.parsers import MultiPartParser
from organizations.models import (
    Organization,
    OrganizationMembership,
)
from organizations.permissions import (
    IsOrganizationAdmin,
    IsOrganizationCustomer,
    IsOrganizationMember,
)
from rest_framework.parsers import MultiPartParser, FormParser



from django.http import FileResponse

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

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
    TicketAttachment,
    TicketCategory,
    TicketHistory,
    TicketMessage,
)

from .permissions import (
    IsTicketOwnerOrOrganizationStaff,
)

from .serializers import (
    TicketAttachmentSerializer,
    TicketCategorySerializer,
    TicketHistorySerializer,
    TicketMessageSerializer,
    TicketSerializer,
)

class OrganizationMixin:
    def get_organization(self):
        if not hasattr(
            self,
            "_ticket_organization",
        ):
            self._ticket_organization = (
                get_object_or_404(
                    Organization,
                    slug=self.kwargs[
                        "organization_slug"
                    ],
                    is_active=True,
                )
            )

        return self._ticket_organization

    def get_membership(self):
        organization = self.get_organization()

        return (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=self.request.user,
                is_active=True,
            )
            .first()
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Tickets"],
        summary="List tickets",
        description=(
            "Returns tickets visible to the authenticated "
            "user in the selected organization. Customers "
            "only see their own tickets."
        ),
    ),
    retrieve=extend_schema(
        tags=["Tickets"],
        summary="Get ticket",
    ),
    create=extend_schema(
        tags=["Tickets"],
        summary="Create ticket",
        description=(
            "Creates a ticket for an authenticated customer "
            "in the selected organization."
        ),
    ),
    update=extend_schema(
        tags=["Tickets"],
        summary="Update ticket",
    ),
    partial_update=extend_schema(
        tags=["Tickets"],
        summary="Partially update ticket",
    ),
    destroy=extend_schema(
        tags=["Tickets"],
        summary="Delete ticket",
        description=(
            "Deletes a ticket. Only an organization admin "
            "can perform this operation."
        ),
    ),
)
class TicketViewSet(
    OrganizationMixin,
    viewsets.ModelViewSet,
):
    serializer_class = TicketSerializer

    filterset_fields = [
        "status",
        "priority",
        "category",
    ]

    search_fields = [
        "title",
        "description",
        "customer__username",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "priority",
        "status",
    ]

    def get_queryset(self):
        organization = self.get_organization()

        queryset = (
            Ticket.objects
            .filter(
                organization=organization,
            )
            .select_related(
                "organization",
                "customer",
                "assigned_agent",
                "category",
            )
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

    def perform_create(
        self,
        serializer,
    ):
        serializer.save(
            organization=self.get_organization(),
            customer=self.request.user,
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Tickets"],
        summary="List ticket categories",
    ),
    retrieve=extend_schema(
        tags=["Tickets"],
        summary="Get ticket category",
    ),
)
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
        organization = self.get_organization()

        return (
            TicketCategory.objects
            .filter(
                organization=organization,
            )
            .order_by(
                "name",
            )
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Tickets"],
        summary="List ticket messages",
        description=(
            "Returns conversation messages for a ticket."
        ),
    ),
    post=extend_schema(
        tags=["Tickets"],
        summary="Send ticket message",
        description=(
            "Creates a new message on a ticket."
        ),
    ),
)
class TicketMessageListCreateView(
    OrganizationMixin,
    generics.ListCreateAPIView,
):
    serializer_class = TicketMessageSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_ticket(self):
        organization = self.get_organization()

        ticket = get_object_or_404(
            Ticket.objects.select_related(
                "organization",
                "customer",
                "assigned_agent",
            ),
            pk=self.kwargs["ticket_id"],
            organization=organization,
        )

        membership = self.get_membership()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if (
            membership.role
            == OrganizationMembership.Role.CUSTOMER
            and ticket.customer_id
            != self.request.user.id
        ):
            raise PermissionDenied(
                "You do not have permission "
                "to access this ticket."
            )

        return ticket

    def get_queryset(self):
        ticket = self.get_ticket()

        return (
            TicketMessage.objects
            .filter(
                ticket=ticket,
            )
            .select_related(
                "ticket",
                "sender",
            )
            .order_by(
                "created_at",
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        ticket = self.get_ticket()

        serializer.save(
            ticket=ticket,
            sender=self.request.user,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Tickets"],
        summary="Get ticket history",
        description=(
            "Returns the audit history for a ticket. "
            "Only organization agents and admins "
            "can access ticket history."
        ),
    ),
)
class TicketHistoryListView(
    OrganizationMixin,
    generics.ListAPIView,
):
    serializer_class = TicketHistorySerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_ticket(self):
        organization = self.get_organization()

        ticket = get_object_or_404(
            Ticket,
            pk=self.kwargs["ticket_id"],
            organization=organization,
        )

        membership = self.get_membership()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission "
                "to view ticket history."
            )

        return ticket

    def get_queryset(self):
        ticket = self.get_ticket()

        return (
            TicketHistory.objects
            .filter(
                ticket=ticket,
            )
            .select_related(
                "ticket",
                "changed_by",
            )
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Tickets"],
        summary="List ticket attachments",
        description=(
            "Returns attachments belonging to a ticket."
        ),
    ),
    post=extend_schema(
        tags=["Tickets"],
        summary="Upload ticket attachment",
        description=(
            "Uploads an attachment to a ticket. "
            "File size and content type validation "
            "are applied by the serializer."
        ),
    ),
)
class TicketAttachmentListCreateView(
    OrganizationMixin,
    generics.ListCreateAPIView,
):
    serializer_class = TicketAttachmentSerializer

    permission_classes = [
        IsAuthenticated,
    ]
    parser_classes = [MultiPartParser, FormParser]

    def get_ticket(self):
        organization = self.get_organization()

        ticket = get_object_or_404(
            Ticket.objects.select_related(
                "organization",
                "customer",
                "assigned_agent",
            ),
            pk=self.kwargs["ticket_id"],
            organization=organization,
        )

        membership = self.get_membership()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if (
            membership.role
            == OrganizationMembership.Role.CUSTOMER
            and ticket.customer_id
            != self.request.user.id
        ):
            raise PermissionDenied(
                "You do not have permission "
                "to access attachments for this ticket."
            )

        return ticket

    def get_queryset(self):
        ticket = self.get_ticket()

        return (
            TicketAttachment.objects
            .filter(
                ticket=ticket,
            )
            .select_related(
                "ticket",
                "uploaded_by",
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        ticket = self.get_ticket()

        uploaded_file = (
            serializer.validated_data["file"]
        )

        serializer.save(
            ticket=ticket,
            uploaded_by=self.request.user,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            content_type=(
                uploaded_file.content_type
            ),
        )


class TicketAttachmentDownloadView(
    OrganizationMixin,
    APIView,
):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Tickets"],
        summary="Download ticket attachment",
        description=(
            "Securely downloads a ticket attachment after "
            "organization and ticket permission checks."
        ),
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="Attachment file",
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
        attachment_id,
    ):
        organization = self.get_organization()

        attachment = get_object_or_404(
            TicketAttachment.objects
            .select_related(
                "ticket",
                "ticket__organization",
                "ticket__customer",
                "uploaded_by",
            ),
            pk=attachment_id,
            ticket__organization=organization,
        )

        membership = self.get_membership()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        ticket = attachment.ticket

        if (
            membership.role
            == OrganizationMembership.Role.CUSTOMER
            and ticket.customer_id
            != request.user.id
        ):
            raise PermissionDenied(
                "You do not have permission "
                "to download this attachment."
            )

        return FileResponse(
            attachment.file.open("rb"),
            as_attachment=True,
            filename=attachment.file_name,
        )