from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from django.db.models import Count, Q
from rest_framework.exceptions import PermissionDenied
from django.db.models import Avg, DurationField, ExpressionWrapper, F
from rest_framework.exceptions import PermissionDenied
from organizations.models import Organization, OrganizationMembership
from tickets.models import Ticket
from django.utils import timezone

from dashboard.sla import SLA_RESOLUTION_HOURS


class DashboardSummaryView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, organization_slug):

        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
        )

        membership = organization.memberships.filter(
            user=request.user,
            is_active=True,
        ).first()

        if not membership:
            return Response(
                {
                    "detail": "You are not a member of this organization."
                },
                status=403,
            )

        tickets = Ticket.objects.filter(
            organization=organization,
        )

        return Response(
            {
                "total_tickets": tickets.count(),

                "open_tickets": tickets.filter(
                    status="open"
                ).count(),

                "in_progress_tickets": tickets.filter(
                    status="in_progress"
                ).count(),

                "resolved_tickets": tickets.filter(
                    status="resolved"
                ).count(),

                "closed_tickets": tickets.filter(
                    status="closed"
                ).count(),
            }
        )
    
class DashboardPriorityView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, organization_slug):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = organization.memberships.filter(
            user=request.user,
            is_active=True,
        ).first()

        if not membership:
            return Response(
                {
                    "detail": "You are not a member of this organization."
                },
                status=403,
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

    def get(self, request, organization_slug):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True,
        ).first()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission to view agent statistics."
            )

        agents = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                role=OrganizationMembership.Role.AGENT,
                is_active=True,
            )
            .select_related("user")
            .annotate(
                assigned_count=Count(
                    "user__assigned_tickets",
                    filter=Q(
                        user__assigned_tickets__organization=organization,
                    ),
                    distinct=True,
                ),
                resolved_count=Count(
                    "user__assigned_tickets",
                    filter=Q(
                        user__assigned_tickets__organization=organization,
                        user__assigned_tickets__status=Ticket.Status.RESOLVED,
                    ),
                    distinct=True,
                ),
            )
        )

        data = [
            {
                "agent_id": membership.user.id,
                "username": membership.user.username,
                "assigned": membership.assigned_count,
                "resolved": membership.resolved_count,
            }
            for membership in agents
        ]

        return Response(data)
    

class DashboardResolutionMetricsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, organization_slug):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True,
        ).first()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission to view resolution metrics."
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
                average_duration.total_seconds() / 3600,
                2,
            )

        return Response(
            {
                "resolved_tickets": resolved_tickets.count(),
                "average_resolution_hours": average_resolution_hours,
            }
        )
    

class DashboardSLAView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, organization_slug):
        organization = get_object_or_404(
            Organization,
            slug=organization_slug,
            is_active=True,
        )

        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True,
        ).first()

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        if membership.role not in (
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.AGENT,
        ):
            raise PermissionDenied(
                "You do not have permission to view SLA metrics."
            )

        tickets = Ticket.objects.filter(
            organization=organization,
        )

        now = timezone.now()

        total_tickets = 0
        within_sla = 0
        breached = 0

        by_priority = {}

        for priority, target_hours in SLA_RESOLUTION_HOURS.items():
            by_priority[priority] = {
                "target_hours": target_hours,
                "total": 0,
                "within_sla": 0,
                "breached": 0,
            }

        for ticket in tickets:
            target_hours = SLA_RESOLUTION_HOURS.get(
                ticket.priority
            )

            if target_hours is None:
                continue

            total_tickets += 1

            if ticket.resolved_at is not None:
                end_time = ticket.resolved_at
            else:
                end_time = now

            elapsed = end_time - ticket.created_at

            elapsed_hours = (
                elapsed.total_seconds() / 3600
            )

            priority_data = by_priority[
                ticket.priority
            ]

            priority_data["total"] += 1

            if elapsed_hours <= target_hours:
                within_sla += 1
                priority_data["within_sla"] += 1
            else:
                breached += 1
                priority_data["breached"] += 1

        if total_tickets == 0:
            compliance_percentage = 100.0
        else:
            compliance_percentage = round(
                (within_sla / total_tickets) * 100,
                2,
            )

        return Response(
            {
                "total_tickets": total_tickets,
                "within_sla": within_sla,
                "breached": breached,
                "compliance_percentage": compliance_percentage,
                "by_priority": by_priority,
            }
        )