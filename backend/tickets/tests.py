from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

from .models import Ticket, TicketMessage
from .permissions import IsTicketOwnerOrAgent


class TicketPermissionTests(TestCase):
    def setUp(self):
        self.customer1 = User.objects.create_user(
            username="customer1_test",
            password="TestPassword123!",
            role=User.Role.CUSTOMER,
        )

        self.customer2 = User.objects.create_user(
            username="customer2_test",
            password="TestPassword123!",
            role=User.Role.CUSTOMER,
        )

        self.agent = User.objects.create_user(
            username="agent_test",
            password="TestPassword123!",
            role=User.Role.AGENT,
        )

        self.admin = User.objects.create_user(
            username="admin_test",
            password="TestPassword123!",
            is_staff=True,
        )

        self.ticket = Ticket.objects.create(
            title="Test ticket",
            description="Test ticket description",
            customer=self.customer1,
        )

    def request_for(self, user):
        return SimpleNamespace(user=user)

    def test_owner_can_access_ticket(self):
        request = self.request_for(self.customer1)

        self.assertTrue(
            IsTicketOwnerOrAgent().has_object_permission(
                request,
                None,
                self.ticket,
            )
        )

    def test_other_customer_cannot_access_ticket(self):
        request = self.request_for(self.customer2)

        self.assertFalse(
            IsTicketOwnerOrAgent().has_object_permission(
                request,
                None,
                self.ticket,
            )
        )

    def test_agent_can_access_ticket(self):
        request = self.request_for(self.agent)

        self.assertTrue(
            IsTicketOwnerOrAgent().has_object_permission(
                request,
                None,
                self.ticket,
            )
        )

    def test_admin_can_access_ticket(self):
        request = self.request_for(self.admin)

        self.assertTrue(
            IsTicketOwnerOrAgent().has_object_permission(
                request,
                None,
                self.ticket,
            )
        )

    def test_anonymous_user_cannot_access_ticket(self):
        request = self.request_for(AnonymousUser())

        self.assertFalse(
            IsTicketOwnerOrAgent().has_object_permission(
                request,
                None,
                self.ticket,
            )
        )


class TicketMessageAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            username="message_customer",
            password="TestPassword123!",
            role=User.Role.CUSTOMER,
        )

        self.other_customer = User.objects.create_user(
            username="other_customer",
            password="TestPassword123!",
            role=User.Role.CUSTOMER,
        )

        self.agent = User.objects.create_user(
            username="message_agent",
            password="TestPassword123!",
            role=User.Role.AGENT,
        )

        self.ticket = Ticket.objects.create(
            title="Dashboard problem",
            description="Dashboard does not load.",
            customer=self.customer,
            assigned_agent=self.agent,
        )

        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.customer,
            message="The dashboard still does not work.",
        )

        self.url = reverse(
            "ticket-message-list",
            kwargs={
                "ticket_id": self.ticket.id,
            },
        )

    def test_ticket_owner_can_view_messages(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.get(
            self.url,
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
            user=self.agent,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_other_customer_cannot_view_messages(self):
        self.client.force_authenticate(
            user=self.other_customer,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_ticket_owner_can_send_message(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.url,
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
            response.data["sender_username"],
            self.customer.username,
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
            user=self.agent,
        )

        response = self.client.post(
            self.url,
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
            self.agent.id,
        )

    def test_other_customer_cannot_send_message(self):
        self.client.force_authenticate(
            user=self.other_customer,
        )

        response = self.client.post(
            self.url,
            {
                "message": "I should not be able to send this.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class TicketAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer1 = User.objects.create_user(
            username="ticket_customer1",
            password="TestPassword123!",
            role=User.Role.CUSTOMER,
        )

        self.customer2 = User.objects.create_user(
            username="ticket_customer2",
            password="TestPassword123!",
            role=User.Role.CUSTOMER,
        )

        self.agent = User.objects.create_user(
            username="ticket_agent",
            password="TestPassword123!",
            role=User.Role.AGENT,
        )

        self.admin = User.objects.create_user(
            username="ticket_admin",
            password="TestPassword123!",
            is_staff=True,
            is_superuser=True,
        )

        self.ticket1 = Ticket.objects.create(
            title="Customer 1 ticket",
            description="First customer ticket",
            customer=self.customer1,
        )

        self.ticket2 = Ticket.objects.create(
            title="Customer 2 ticket",
            description="Second customer ticket",
            customer=self.customer2,
        )

        self.list_url = reverse("ticket-list")

    def detail_url(self, ticket):
        return reverse(
            "ticket-detail",
            kwargs={"pk": ticket.pk},
        )

    def test_customer_only_sees_own_tickets(self):
        self.client.force_authenticate(
            user=self.customer1,
        )

        response = self.client.get(
            self.list_url,
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
            self.ticket1.id,
        )

    def test_customer_can_retrieve_own_ticket(self):
        self.client.force_authenticate(
            user=self.customer1,
        )

        response = self.client.get(
            self.detail_url(self.ticket1),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.ticket1.id,
        )

    def test_customer_cannot_retrieve_other_customer_ticket(self):
        self.client.force_authenticate(
            user=self.customer1,
        )

        response = self.client.get(
            self.detail_url(self.ticket2),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_can_create_ticket(self):
        self.client.force_authenticate(
            user=self.customer1,
        )

        response = self.client.post(
            self.list_url,
            {
                "title": "New ticket",
                "description": "New ticket description",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["customer"],
            self.customer1.id,
        )

        self.assertEqual(
            response.data["status"],
            Ticket.Status.OPEN,
        )

        self.assertEqual(
            response.data["priority"],
            Ticket.Priority.MEDIUM,
        )

    def test_customer_cannot_modify_managed_fields(self):
        self.client.force_authenticate(
            user=self.customer1,
        )

        response = self.client.patch(
            self.detail_url(self.ticket1),
            {
                "status": Ticket.Status.RESOLVED,
                "priority": Ticket.Priority.URGENT,
                "assigned_agent": self.agent.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.ticket1.refresh_from_db()

        self.assertEqual(
            self.ticket1.status,
            Ticket.Status.OPEN,
        )

        self.assertEqual(
            self.ticket1.priority,
            Ticket.Priority.MEDIUM,
        )

        self.assertIsNone(
            self.ticket1.assigned_agent,
        )

    def test_agent_can_see_all_tickets(self):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_agent_can_assign_and_update_ticket(self):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.patch(
            self.detail_url(self.ticket1),
            {
                "assigned_agent": self.agent.id,
                "priority": Ticket.Priority.HIGH,
                "status": Ticket.Status.IN_PROGRESS,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.ticket1.refresh_from_db()

        self.assertEqual(
            self.ticket1.assigned_agent,
            self.agent,
        )

        self.assertEqual(
            self.ticket1.priority,
            Ticket.Priority.HIGH,
        )

        self.assertEqual(
            self.ticket1.status,
            Ticket.Status.IN_PROGRESS,
        )

    def test_agent_cannot_modify_customer_content(self):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.patch(
            self.detail_url(self.ticket1),
            {
                "title": "Changed by agent",
                "description": "Agent changed description",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.ticket1.refresh_from_db()

        self.assertEqual(
            self.ticket1.title,
            "Customer 1 ticket",
        )

    def test_customer_cannot_delete_ticket(self):
        self.client.force_authenticate(
            user=self.customer1,
        )

        response = self.client.delete(
            self.detail_url(self.ticket1),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Ticket.objects.filter(
                pk=self.ticket1.pk,
            ).exists()
        )

    def test_agent_cannot_delete_ticket(self):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.delete(
            self.detail_url(self.ticket1),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_delete_ticket(self):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.delete(
            self.detail_url(self.ticket1),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Ticket.objects.filter(
                pk=self.ticket1.pk,
            ).exists()
        )

    def test_anonymous_user_cannot_list_tickets(self):
        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )