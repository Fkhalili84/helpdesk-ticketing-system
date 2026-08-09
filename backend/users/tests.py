from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from .models import User
from .permissions import IsAgentOrAdmin, IsCustomer


class RolePermissionTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer_test",
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

    def request_for(self, user):
        return SimpleNamespace(user=user)

    def test_customer_permission_allows_customer(self):
        request = self.request_for(self.customer)

        self.assertTrue(
            IsCustomer().has_permission(request, None)
        )

    def test_customer_permission_denies_agent(self):
        request = self.request_for(self.agent)

        self.assertFalse(
            IsCustomer().has_permission(request, None)
        )

    def test_agent_permission_allows_agent(self):
        request = self.request_for(self.agent)

        self.assertTrue(
            IsAgentOrAdmin().has_permission(request, None)
        )

    def test_agent_permission_allows_admin(self):
        request = self.request_for(self.admin)

        self.assertTrue(
            IsAgentOrAdmin().has_permission(request, None)
        )

    def test_permissions_deny_anonymous_user(self):
        request = self.request_for(AnonymousUser())

        self.assertFalse(
            IsCustomer().has_permission(request, None)
        )

        self.assertFalse(
            IsAgentOrAdmin().has_permission(request, None)
        )