from django.db.models import (
    Avg,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    Q,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
)

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import (
    Organization,
    OrganizationMembership,
)
from tickets.models import Ticket

from dashboard.sla import SLA_RESOLUTION_HOURS


class DashboardSummaryView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Dashboard"],
        summary="Get dashboard summary",
        description=(
            "Returns the total number of tickets and "
            "ticket counts grouped by status for the "
            "selected organization."
        ),
        responses={
            200: inline_serializer(
                name="DashboardSummaryResponse",
                fields={
                    "total_tickets": serializers.IntegerField(),
                    "open_tickets": serializers.IntegerField(),
                    "in_progress_tickets": serializers.IntegerField(),
                    "resolved_tickets": serializers.IntegerField(),
                    "closed_tickets": serializers.IntegerField(),
                },
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        tickets = Ticket.objects.filter(
            organization=organization,
        )

        return Response(
            {
                "total_tickets": tickets.count(),

                "open_tickets": tickets.filter(
                    status=Ticket.Status.OPEN,
                ).count(),

                "in_progress_tickets": tickets.filter(
                    status=Ticket.Status.IN_PROGRESS,
                ).count(),

                "resolved_tickets": tickets.filter(
                    status=Ticket.Status.RESOLVED,
                ).count(),

                "closed_tickets": tickets.filter(
                    status=Ticket.Status.CLOSED,
                ).count(),
            }
        )


class DashboardPriorityView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Dashboard"],
        summary="Get ticket priority statistics",
        description=(
            "Returns ticket counts grouped by priority "
            "for the selected organization."
        ),
        responses={
            200: inline_serializer(
                name="DashboardPriorityResponse",
                fields={
                    "low": serializers.IntegerField(),
                    "medium": serializers.IntegerField(),
                    "high": serializers.IntegerField(),
                    "urgent": serializers.IntegerField(),
                },
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        tickets = Ticket.objects.filter(
            organization=organization,
        )

        return Response(
            {
                "low": tickets.filter(
                    priority=Ticket.Priority.LOW,
                ).count(),

                "medium": tickets.filter(
                    priority=Ticket.Priority.MEDIUM,
                ).count(),

                "high": tickets.filter(
                    priority=Ticket.Priority.HIGH,
                ).count(),

                "urgent": tickets.filter(
                    priority=Ticket.Priority.URGENT,
                ).count(),
            }
        )


class DashboardAgentPerformanceView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Dashboard"],
        summary="Get agent performance statistics",
        description=(
            "Returns assigned and resolved ticket counts "
            "for active agents in the selected organization. "
            "Only organization admins and agents can access "
            "this endpoint."
        ),
        responses={
            200: inline_serializer(
                name="DashboardAgentPerformanceResponse",
                many=True,
                fields={
                    "agent_id": serializers.IntegerField(),
                    "username": serializers.CharField(),
                    "assigned": serializers.IntegerField(),
                    "resolved": serializers.IntegerField(),
                },
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission to view "
                "agent statistics."
            )

        agents = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                role=OrganizationMembership.Role.AGENT,
                is_active=True,
            )
            .select_related(
                "user",
            )
            .annotate(
                assigned_count=Count(
                    "user__assigned_tickets",
                    filter=Q(
                        user__assigned_tickets__organization=(
                            organization
                        ),
                    ),
                    distinct=True,
                ),
                resolved_count=Count(
                    "user__assigned_tickets",
                    filter=Q(
                        user__assigned_tickets__organization=(
                            organization
                        ),
                        user__assigned_tickets__status=(
                            Ticket.Status.RESOLVED
                        ),
                    ),
                    distinct=True,
                ),
            )
        )

        data = [
            {
                "agent_id": agent_membership.user.id,
                "username": agent_membership.user.username,
                "assigned": agent_membership.assigned_count,
                "resolved": agent_membership.resolved_count,
            }
            for agent_membership in agents
        ]

        return Response(
            data
        )


class DashboardResolutionMetricsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Dashboard"],
        summary="Get resolution metrics",
        description=(
            "Returns the number of resolved tickets and "
            "the average ticket resolution time in hours. "
            "Closed tickets with a resolution timestamp "
            "are also included."
        ),
        responses={
            200: inline_serializer(
                name="DashboardResolutionMetricsResponse",
                fields={
                    "resolved_tickets": serializers.IntegerField(),
                    "average_resolution_hours": serializers.FloatField(),
                },
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission to view "
                "resolution metrics."
            )

        resolved_tickets = Ticket.objects.filter(
            organization=organization,
            status__in=(
                Ticket.Status.RESOLVED,
                Ticket.Status.CLOSED,
            ),
            resolved_at__isnull=False,
        )

        resolution_duration = ExpressionWrapper(
            F("resolved_at") - F("created_at"),
            output_field=DurationField(),
        )

        metrics = resolved_tickets.aggregate(
            average_resolution_time=Avg(
                resolution_duration,
            )
        )

        average_duration = metrics[
            "average_resolution_time"
        ]

        if average_duration is None:
            average_resolution_hours = 0.0

        else:
            average_resolution_hours = round(
                average_duration.total_seconds()
                / 3600,
                2,
            )

        return Response(
            {
                "resolved_tickets": (
                    resolved_tickets.count()
                ),
                "average_resolution_hours": (
                    average_resolution_hours
                ),
            }
        )


class DashboardSLAView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Dashboard"],
        summary="Get SLA statistics",
        description=(
            "Returns SLA compliance statistics including "
            "tickets within SLA, breached tickets, overall "
            "compliance percentage, and statistics grouped "
            "by ticket priority. Only organization admins "
            "and agents can access this endpoint."
        ),
        responses={
            200: inline_serializer(
                name="DashboardSLAResponse",
                fields={
                    "total_tickets": serializers.IntegerField(),
                    "within_sla": serializers.IntegerField(),
                    "breached": serializers.IntegerField(),
                    "compliance_percentage": serializers.FloatField(),
                    "by_priority": serializers.DictField(),
                },
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission to view "
                "SLA metrics."
            )

        tickets = Ticket.objects.filter(
            organization=organization,
        )

        now = timezone.now()

        total_tickets = 0
        within_sla = 0
        breached = 0

        by_priority = {}

        for (
            priority,
            target_hours,
        ) in SLA_RESOLUTION_HOURS.items():

            by_priority[
                priority
            ] = {
                "target_hours": target_hours,
                "total": 0,
                "within_sla": 0,
                "breached": 0,
            }

        for ticket in tickets:
            target_hours = (
                SLA_RESOLUTION_HOURS.get(
                    ticket.priority
                )
            )

            if target_hours is None:
                continue

            total_tickets += 1

            if ticket.resolved_at is not None:
                end_time = ticket.resolved_at

            else:
                end_time = now

            elapsed = (
                end_time
                - ticket.created_at
            )

            elapsed_hours = (
                elapsed.total_seconds()
                / 3600
            )

            priority_data = (
                by_priority[
                    ticket.priority
                ]
            )

            priority_data[
                "total"
            ] += 1

            if elapsed_hours <= target_hours:
                within_sla += 1

                priority_data[
                    "within_sla"
                ] += 1

            else:
                breached += 1

                priority_data[
                    "breached"
                ] += 1

        if total_tickets == 0:
            compliance_percentage = 100.0

        else:
            compliance_percentage = round(
                (
                    within_sla
                    / total_tickets
                )
                * 100,
                2,
            )

        return Response(
            {
                "total_tickets": total_tickets,
                "within_sla": within_sla,
                "breached": breached,
                "compliance_percentage": (
                    compliance_percentage
                ),
                "by_priority": by_priority,
            }
        )