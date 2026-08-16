from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from organizations.models import (
    Organization,
    OrganizationMembership,
)
from users.models import User

from .models import (
    Ticket,
    TicketCategory,
    TicketMessage,
)


class TicketAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # ---------------------------------------------------------
        # Organizations
        # ---------------------------------------------------------

        self.organization_a = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.organization_b = Organization.objects.create(
            name="ABC Company",
            slug="abc",
        )

        # ---------------------------------------------------------
        # Users
        # ---------------------------------------------------------

        self.customer_a1 = User.objects.create_user(
            username="customer_a1",
            password="TestPassword123!",
            email="customer_a1@example.com",
        )

        self.customer_a2 = User.objects.create_user(
            username="customer_a2",
            password="TestPassword123!",
            email="customer_a2@example.com",
        )

        self.agent_a = User.objects.create_user(
            username="agent_a",
            password="TestPassword123!",
            email="agent_a@example.com",
        )

        self.admin_a = User.objects.create_user(
            username="admin_a",
            password="TestPassword123!",
            email="admin_a@example.com",
        )

        self.customer_b = User.objects.create_user(
            username="customer_b",
            password="TestPassword123!",
            email="customer_b@example.com",
        )

        self.agent_b = User.objects.create_user(
            username="agent_b",
            password="TestPassword123!",
            email="agent_b@example.com",
        )

        # ---------------------------------------------------------
        # Memberships - Organization A
        # ---------------------------------------------------------

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.customer_a1,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.customer_a2,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.agent_a,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.admin_a,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

        # ---------------------------------------------------------
        # Memberships - Organization B
        # ---------------------------------------------------------

        OrganizationMembership.objects.create(
            organization=self.organization_b,
            user=self.customer_b,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_b,
            user=self.agent_b,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        # ---------------------------------------------------------
        # Categories
        # ---------------------------------------------------------

        self.category_a = TicketCategory.objects.create(
            organization=self.organization_a,
            name="Technical",
            description="Technical issues",
        )

        self.category_b = TicketCategory.objects.create(
            organization=self.organization_b,
            name="Technical",
            description="Technical issues for ABC",
        )

        # ---------------------------------------------------------
        # Tickets
        # ---------------------------------------------------------

        self.ticket_a1 = Ticket.objects.create(
            organization=self.organization_a,
            customer=self.customer_a1,
            category=self.category_a,
            title="Customer A1 ticket",
            description="First NexaCloud ticket",
        )

        self.ticket_a2 = Ticket.objects.create(
            organization=self.organization_a,
            customer=self.customer_a2,
            category=self.category_a,
            title="Customer A2 ticket",
            description="Second NexaCloud ticket",
        )

        self.ticket_b = Ticket.objects.create(
            organization=self.organization_b,
            customer=self.customer_b,
            category=self.category_b,
            title="Customer B ticket",
            description="ABC Company ticket",
        )

    # -------------------------------------------------------------
    # URL helpers
    # -------------------------------------------------------------

    def list_url(self, organization):
        return reverse(
            "ticket-list",
            kwargs={
                "organization_slug": organization.slug,
            },
        )

    def detail_url(self, organization, ticket):
        return reverse(
            "ticket-detail",
            kwargs={
                "organization_slug": organization.slug,
                "pk": ticket.pk,
            },
        )

    def category_list_url(self, organization):
        return reverse(
            "ticket-category-list",
            kwargs={
                "organization_slug": organization.slug,
            },
        )

    # -------------------------------------------------------------
    # Customer visibility
    # -------------------------------------------------------------

    def test_customer_only_sees_own_tickets(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.get(
            self.list_url(self.organization_a),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            self.ticket_a1.id,
        )

    def test_customer_can_retrieve_own_ticket(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.get(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.ticket_a1.id,
        )

    def test_customer_cannot_retrieve_other_customer_ticket(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.get(
            self.detail_url(
                self.organization_a,
                self.ticket_a2,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # -------------------------------------------------------------
    # Ticket creation
    # -------------------------------------------------------------

    def test_customer_can_create_ticket_in_own_organization(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.post(
            self.list_url(self.organization_a),
            {
                "title": "New ticket",
                "description": "New ticket description",
                "category": self.category_a.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        created_ticket = Ticket.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            created_ticket.customer,
            self.customer_a1,
        )

        self.assertEqual(
            created_ticket.organization,
            self.organization_a,
        )

        self.assertEqual(
            created_ticket.category,
            self.category_a,
        )

        self.assertEqual(
            created_ticket.status,
            Ticket.Status.OPEN,
        )

        self.assertEqual(
            created_ticket.priority,
            Ticket.Priority.MEDIUM,
        )

    def test_customer_cannot_use_category_from_other_organization(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.post(
            self.list_url(self.organization_a),
            {
                "title": "Invalid category ticket",
                "description": "Cross tenant category test",
                "category": self.category_b.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # -------------------------------------------------------------
    # Customer restrictions
    # -------------------------------------------------------------

    def test_customer_cannot_modify_managed_fields(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.patch(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
            {
                "status": Ticket.Status.RESOLVED,
                "priority": Ticket.Priority.URGENT,
                "assigned_agent": self.agent_a.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.ticket_a1.refresh_from_db()

        self.assertEqual(
            self.ticket_a1.status,
            Ticket.Status.OPEN,
        )

        self.assertEqual(
            self.ticket_a1.priority,
            Ticket.Priority.MEDIUM,
        )

        self.assertIsNone(
            self.ticket_a1.assigned_agent,
        )

    # -------------------------------------------------------------
    # Agent visibility
    # -------------------------------------------------------------

    def test_agent_sees_all_tickets_in_own_organization(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.get(
            self.list_url(self.organization_a),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            ticket["id"]
            for ticket in response.data
        }

        self.assertEqual(
            returned_ids,
            {
                self.ticket_a1.id,
                self.ticket_a2.id,
            },
        )

        self.assertNotIn(
            self.ticket_b.id,
            returned_ids,
        )

    def test_agent_cannot_access_organization_without_membership(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.get(
            self.list_url(self.organization_b),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # -------------------------------------------------------------
    # Tenant isolation
    # -------------------------------------------------------------

    def test_ticket_from_other_organization_returns_404(self):
        self.client.force_authenticate(
            user=self.agent_b,
        )

        response = self.client.get(
            self.detail_url(
                self.organization_b,
                self.ticket_a1,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # -------------------------------------------------------------
    # Agent ticket management
    # -------------------------------------------------------------

    def test_agent_can_assign_and_update_ticket(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.patch(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
            {
                "assigned_agent": self.agent_a.id,
                "priority": Ticket.Priority.HIGH,
                "status": Ticket.Status.IN_PROGRESS,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.ticket_a1.refresh_from_db()

        self.assertEqual(
            self.ticket_a1.assigned_agent,
            self.agent_a,
        )

        self.assertEqual(
            self.ticket_a1.priority,
            Ticket.Priority.HIGH,
        )

        self.assertEqual(
            self.ticket_a1.status,
            Ticket.Status.IN_PROGRESS,
        )

    def test_agent_cannot_assign_agent_from_other_organization(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.patch(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
            {
                "assigned_agent": self.agent_b.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.ticket_a1.refresh_from_db()

        self.assertIsNone(
            self.ticket_a1.assigned_agent,
        )

    def test_agent_cannot_modify_customer_content(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.patch(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
            {
                "title": "Changed by agent",
                "description": "Changed description",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.ticket_a1.refresh_from_db()

        self.assertEqual(
            self.ticket_a1.title,
            "Customer A1 ticket",
        )

        self.assertEqual(
            self.ticket_a1.description,
            "First NexaCloud ticket",
        )

    def test_resolved_status_sets_resolved_at(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.patch(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
            {
                "status": Ticket.Status.RESOLVED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.ticket_a1.refresh_from_db()

        self.assertEqual(
            self.ticket_a1.status,
            Ticket.Status.RESOLVED,
        )

        self.assertIsNotNone(
            self.ticket_a1.resolved_at,
        )

    # -------------------------------------------------------------
    # Delete permissions
    # -------------------------------------------------------------

    def test_customer_cannot_delete_ticket(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.delete(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Ticket.objects.filter(
                pk=self.ticket_a1.pk,
            ).exists()
        )

    def test_agent_cannot_delete_ticket(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.delete(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Ticket.objects.filter(
                pk=self.ticket_a1.pk,
            ).exists()
        )

    def test_organization_admin_can_delete_ticket(self):
        self.client.force_authenticate(
            user=self.admin_a,
        )

        response = self.client.delete(
            self.detail_url(
                self.organization_a,
                self.ticket_a1,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Ticket.objects.filter(
                pk=self.ticket_a1.pk,
            ).exists()
        )

    # -------------------------------------------------------------
    # Category tenant isolation
    # -------------------------------------------------------------

    def test_category_list_only_contains_current_organization_categories(self):
        self.client.force_authenticate(
            user=self.customer_a1,
        )

        response = self.client.get(
            self.category_list_url(
                self.organization_a,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            category["id"]
            for category in response.data
        }

        self.assertIn(
            self.category_a.id,
            returned_ids,
        )

        self.assertNotIn(
            self.category_b.id,
            returned_ids,
        )

    # -------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------

    def test_anonymous_user_cannot_list_tickets(self):
        response = self.client.get(
            self.list_url(
                self.organization_a,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class TicketMessageAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # ---------------------------------------------------------
        # Organizations
        # ---------------------------------------------------------

        self.organization_a = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.organization_b = Organization.objects.create(
            name="ABC Company",
            slug="abc",
        )

        # ---------------------------------------------------------
        # Users
        # ---------------------------------------------------------

        self.customer = User.objects.create_user(
            username="message_customer",
            password="TestPassword123!",
        )

        self.other_customer = User.objects.create_user(
            username="other_customer",
            password="TestPassword123!",
        )

        self.agent_a = User.objects.create_user(
            username="message_agent_a",
            password="TestPassword123!",
        )

        self.agent_b = User.objects.create_user(
            username="message_agent_b",
            password="TestPassword123!",
        )

        # ---------------------------------------------------------
        # Memberships
        # ---------------------------------------------------------

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.customer,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.other_customer,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_a,
            user=self.agent_a,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization_b,
            user=self.agent_b,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        # ---------------------------------------------------------
        # Ticket
        # ---------------------------------------------------------

        self.ticket = Ticket.objects.create(
            organization=self.organization_a,
            title="Dashboard problem",
            description="Dashboard does not load.",
            customer=self.customer,
            assigned_agent=self.agent_a,
        )

        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.customer,
            message="The dashboard still does not work.",
        )

    def message_url(self, organization, ticket):
        return reverse(
            "ticket-message-list",
            kwargs={
                "organization_slug": organization.slug,
                "ticket_id": ticket.id,
            },
        )

    # -------------------------------------------------------------
    # Reading messages
    # -------------------------------------------------------------

    def test_ticket_owner_can_view_messages(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.get(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["message"],
            "The dashboard still does not work.",
        )

    def test_agent_can_view_messages(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.get(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_other_customer_cannot_view_messages(self):
        self.client.force_authenticate(
            user=self.other_customer,
        )

        response = self.client.get(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_other_organization_agent_cannot_access_messages(self):
        self.client.force_authenticate(
            user=self.agent_b,
        )

        response = self.client.get(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_ticket_cannot_be_accessed_through_wrong_organization_url(self):
        self.client.force_authenticate(
            user=self.agent_b,
        )

        response = self.client.get(
            self.message_url(
                self.organization_b,
                self.ticket,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # -------------------------------------------------------------
    # Sending messages
    # -------------------------------------------------------------

    def test_ticket_owner_can_send_message(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
            {
                "message": "Here is some more information.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["sender"],
            self.customer.id,
        )

        self.assertEqual(
            response.data["ticket"],
            self.ticket.id,
        )

        self.assertTrue(
            TicketMessage.objects.filter(
                ticket=self.ticket,
                sender=self.customer,
                message="Here is some more information.",
            ).exists()
        )

    def test_agent_can_send_message(self):
        self.client.force_authenticate(
            user=self.agent_a,
        )

        response = self.client.post(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
            {
                "message": "I am investigating the issue.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["sender"],
            self.agent_a.id,
        )

    def test_other_customer_cannot_send_message(self):
        self.client.force_authenticate(
            user=self.other_customer,
        )

        response = self.client.post(
            self.message_url(
                self.organization_a,
                self.ticket,
            ),
            {
                "message": "Unauthorized message.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )