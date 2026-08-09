from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from users.models import User

from .models import Ticket
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