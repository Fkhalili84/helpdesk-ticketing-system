from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from organizations.models import Organization, OrganizationMembership
from tickets.models import Ticket
from datetime import timedelta
from django.utils import timezone


class DashboardAPITests(APITestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.agent = User.objects.create_user(
            username="dashboard_agent",
            password="Password123!",
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.agent,
            role="agent",
            is_active=True,
        )

        self.ticket_open = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Open ticket",
            description="Test",
            status="open",
        )

        self.ticket_resolved = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Resolved ticket",
            description="Test",
            status="resolved",
        )

    def test_agent_can_view_dashboard_summary(self):
        self.client.force_authenticate(
            user=self.agent
        )

        response = self.client.get(
            reverse(
                "dashboard-summary",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["total_tickets"],
            2,
        )

        self.assertEqual(
            response.data["open_tickets"],
            1,
        )

        self.assertEqual(
            response.data["resolved_tickets"],
            1,
        )


    def test_user_without_membership_cannot_view_dashboard(self):
        user = User.objects.create_user(
            username="outside_user",
            password="Password123!",
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.get(
            reverse(
                "dashboard-summary",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_dashboard_priority_statistics(self):
        self.client.force_authenticate(
            user=self.agent,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="High priority ticket",
            description="Test",
            priority=Ticket.Priority.HIGH,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Urgent priority ticket",
            description="Test",
            priority=Ticket.Priority.URGENT,
        )

        response = self.client.get(
            reverse(
                "dashboard-priorities",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["high"],
            1,
        )

        self.assertEqual(
            response.data["urgent"],
            1,
        )

        # دو Ticket ساخته‌شده در setUp به‌صورت پیش‌فرض MEDIUM هستند.
        self.assertEqual(
            response.data["medium"],
            2,
        )

        self.assertEqual(
            response.data["low"],
            0,
        )


    def test_user_without_membership_cannot_view_priority_statistics(self):
        outside_user = User.objects.create_user(
            username="outside_priority_user",
            password="Password123!",
        )

        self.client.force_authenticate(
            user=outside_user,
        )

        response = self.client.get(
            reverse(
                "dashboard-priorities",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_agent_performance_statistics(self):
        second_agent = User.objects.create_user(
            username="dashboard_agent_2",
            password="Password123!",
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=second_agent,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            assigned_agent=self.agent,
            title="Agent ticket 1",
            description="Test",
            status=Ticket.Status.OPEN,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            assigned_agent=self.agent,
            title="Agent ticket 2",
            description="Test",
            status=Ticket.Status.RESOLVED,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            assigned_agent=second_agent,
            title="Second agent ticket",
            description="Test",
            status=Ticket.Status.RESOLVED,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-agents",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        agents = {
            item["username"]: item
            for item in response.data
        }

        self.assertIn(
            self.agent.username,
            agents,
        )

        self.assertIn(
            second_agent.username,
            agents,
        )

        self.assertEqual(
            agents[self.agent.username]["assigned"],
            2,
        )

        self.assertEqual(
            agents[self.agent.username]["resolved"],
            1,
        )

        self.assertEqual(
            agents[second_agent.username]["assigned"],
            1,
        )

        self.assertEqual(
            agents[second_agent.username]["resolved"],
            1,
        )

    def test_customer_cannot_view_agent_performance(self):
        customer = User.objects.create_user(
            username="dashboard_customer",
            password="Password123!",
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=customer,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        self.client.force_authenticate(
            user=customer,
        )

        response = self.client.get(
            reverse(
                "dashboard-agents",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_agent_performance_does_not_include_other_organization_tickets(self):
        other_organization = Organization.objects.create(
            name="Other Company",
            slug="other-company",
        )

        OrganizationMembership.objects.create(
            organization=other_organization,
            user=self.agent,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            assigned_agent=self.agent,
            title="Current organization ticket",
            description="Test",
            status=Ticket.Status.RESOLVED,
        )

        Ticket.objects.create(
            organization=other_organization,
            customer=self.agent,
            assigned_agent=self.agent,
            title="Other organization ticket",
            description="Should not be counted",
            status=Ticket.Status.RESOLVED,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-agents",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        agent_data = next(
            item
            for item in response.data
            if item["username"] == self.agent.username
        )

        self.assertEqual(
            agent_data["assigned"],
            1,
        )

        self.assertEqual(
            agent_data["resolved"],
            1,
        )

    def test_resolution_metrics_calculates_average_resolution_time(self):
        now = timezone.now()

        ticket_1 = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Resolved ticket 1",
            description="Test",
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        ticket_2 = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Resolved ticket 2",
            description="Test",
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        # Ticket 1 = 2 hours
        Ticket.objects.filter(
            pk=ticket_1.pk,
        ).update(
            created_at=now - timedelta(hours=2),
            resolved_at=now,
        )

        # Ticket 2 = 6 hours
        Ticket.objects.filter(
            pk=ticket_2.pk,
        ).update(
            created_at=now - timedelta(hours=6),
            resolved_at=now,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-resolution",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["resolved_tickets"],
            2,
        )

        self.assertEqual(
            response.data["average_resolution_hours"],
            4.0,
        )

    def test_resolution_metrics_excludes_unresolved_tickets(self):
        now = timezone.now()

        resolved_ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Resolved ticket",
            description="Test",
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=resolved_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=3),
            resolved_at=now,
        )

        Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Open ticket for metrics",
            description="Test",
            status=Ticket.Status.OPEN,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-resolution",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["resolved_tickets"],
            1,
        )

        self.assertEqual(
            response.data["average_resolution_hours"],
            3.0,
        )

    def test_resolution_metrics_do_not_include_other_organization_tickets(self):
        now = timezone.now()

        other_organization = Organization.objects.create(
            name="Other Company",
            slug="other-company-resolution",
        )

        OrganizationMembership.objects.create(
            organization=other_organization,
            user=self.agent,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        own_ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Own organization ticket",
            description="Test",
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        other_ticket = Ticket.objects.create(
            organization=other_organization,
            customer=self.agent,
            title="Other organization ticket",
            description="Test",
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=own_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=2),
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=other_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=20),
            resolved_at=now,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-resolution",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["resolved_tickets"],
            1,
        )

        self.assertEqual(
            response.data["average_resolution_hours"],
            2.0,
        )

    def test_sla_statistics_calculate_within_and_breached_tickets(self):
        Ticket.objects.filter(
            organization=self.organization,
        ).delete()

        now = timezone.now()

        within_sla_ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Urgent within SLA",
            description="Test",
            priority=Ticket.Priority.URGENT,
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        breached_ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Urgent breached SLA",
            description="Test",
            priority=Ticket.Priority.URGENT,
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=within_sla_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=2),
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=breached_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=3),
            resolved_at=now,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-sla",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["total_tickets"],
            2,
        )

        self.assertEqual(
            response.data["within_sla"],
            1,
        )

        self.assertEqual(
            response.data["breached"],
            1,
        )

        self.assertEqual(
            response.data["compliance_percentage"],
            50.0,
        )

        urgent_data = response.data["by_priority"][
            Ticket.Priority.URGENT
        ]

        self.assertEqual(
            urgent_data["target_hours"],
            2,
        )

        self.assertEqual(
            urgent_data["total"],
            2,
        )

        self.assertEqual(
            urgent_data["within_sla"],
            1,
        )

        self.assertEqual(
            urgent_data["breached"],
            1,
        )

    def test_unresolved_overdue_ticket_is_sla_breached(self):
        Ticket.objects.filter(
            organization=self.organization,
        ).delete()

        ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Overdue high priority ticket",
            description="Test",
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.OPEN,
        )

        Ticket.objects.filter(
            pk=ticket.pk,
        ).update(
            created_at=timezone.now() - timedelta(hours=10),
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-sla",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["total_tickets"],
            1,
        )

        self.assertEqual(
            response.data["within_sla"],
            0,
        )

        self.assertEqual(
            response.data["breached"],
            1,
        )

        self.assertEqual(
            response.data["compliance_percentage"],
            0.0,
        )

        high_data = response.data["by_priority"][
            Ticket.Priority.HIGH
        ]

        self.assertEqual(
            high_data["target_hours"],
            8,
        )

        self.assertEqual(
            high_data["breached"],
            1,
        )

    def test_sla_statistics_do_not_include_other_organization_tickets(self):
        Ticket.objects.filter(
            organization=self.organization,
        ).delete()

        other_organization = Organization.objects.create(
            name="Other SLA Company",
            slug="other-sla-company",
        )

        OrganizationMembership.objects.create(
            organization=other_organization,
            user=self.agent,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        now = timezone.now()

        own_ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.agent,
            title="Own organization ticket",
            description="Test",
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        other_ticket = Ticket.objects.create(
            organization=other_organization,
            customer=self.agent,
            title="Other organization ticket",
            description="Test",
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.RESOLVED,
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=own_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=4),
            resolved_at=now,
        )

        Ticket.objects.filter(
            pk=other_ticket.pk,
        ).update(
            created_at=now - timedelta(hours=20),
            resolved_at=now,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            reverse(
                "dashboard-sla",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["total_tickets"],
            1,
        )

        self.assertEqual(
            response.data["within_sla"],
            1,
        )

        self.assertEqual(
            response.data["breached"],
            0,
        )

        self.assertEqual(
            response.data["compliance_percentage"],
            100.0,
        )

    def test_customer_cannot_view_sla_statistics(self):
        customer = User.objects.create_user(
            username="sla_customer",
            password="Password123!",
        )
    
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=customer,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )
    
        self.client.force_authenticate(
            user=customer,
        )
    
        response = self.client.get(
            reverse(
                "dashboard-sla",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )