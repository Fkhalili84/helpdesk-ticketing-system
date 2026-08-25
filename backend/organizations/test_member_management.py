from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import (
    Ticket,
    TicketHistory,
)

from users.models import User

from .models import (
    Organization,
    OrganizationMembership,
)


class OrganizationMemberManagementTests(
    APITestCase
):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.other_organization = (
            Organization.objects.create(
                name="Other Company",
                slug="other-member-company",
            )
        )

        self.admin = User.objects.create_user(
            username="member_admin",
            password="Password123!",
            email="admin@example.com",
        )

        self.agent = User.objects.create_user(
            username="member_agent",
            password="Password123!",
            email="agent@example.com",
        )

        self.customer = User.objects.create_user(
            username="member_customer",
            password="Password123!",
            email="customer@example.com",
        )

        self.other_admin = User.objects.create_user(
            username="other_admin",
            password="Password123!",
            email="other@example.com",
        )

        self.admin_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.admin,
                role=OrganizationMembership.Role.ADMIN,
                is_active=True,
            )
        )

        self.agent_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.agent,
                role=OrganizationMembership.Role.AGENT,
                is_active=True,
            )
        )

        self.customer_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.customer,
                role=OrganizationMembership.Role.CUSTOMER,
                is_active=True,
            )
        )

        self.other_admin_membership = (
            OrganizationMembership.objects.create(
                organization=self.other_organization,
                user=self.other_admin,
                role=OrganizationMembership.Role.ADMIN,
                is_active=True,
            )
        )

    def list_url(
        self,
        organization=None,
    ):
        organization = (
            organization
            or self.organization
        )

        return reverse(
            "organization-member-list",
            kwargs={
                "organization_slug":
                    organization.slug,
            },
        )

    def detail_url(
        self,
        membership,
        organization=None,
    ):
        organization = (
            organization
            or self.organization
        )

        return reverse(
            "organization-member-detail",
            kwargs={
                "organization_slug":
                    organization.slug,

                "membership_id":
                    membership.id,
            },
        )

    def get_results(
        self,
        response,
    ):
        if isinstance(
            response.data,
            dict,
        ) and "results" in response.data:
            return response.data["results"]

        return response.data

    # ---------------------------------------------------------
    # List
    # ---------------------------------------------------------

    def test_admin_can_list_organization_members(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = self.get_results(
            response
        )

        returned_ids = {
            item["id"]
            for item in results
        }

        self.assertEqual(
            returned_ids,
            {
                self.admin_membership.id,
                self.agent_membership.id,
                self.customer_membership.id,
            },
        )

        self.assertNotIn(
            self.other_admin_membership.id,
            returned_ids,
        )

    def test_agent_cannot_manage_members(
        self,
    ):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_list_members(
        self,
    ):
        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ---------------------------------------------------------
    # Search / filtering
    # ---------------------------------------------------------

    def test_admin_can_filter_members_by_role(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.get(
            self.list_url(),
            {
                "role":
                    OrganizationMembership.Role.AGENT,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = self.get_results(
            response
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["id"],
            self.agent_membership.id,
        )

    def test_admin_can_search_members(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.get(
            self.list_url(),
            {
                "search": "member_agent",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = self.get_results(
            response
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["username"],
            self.agent.username,
        )

    # ---------------------------------------------------------
    # Role management
    # ---------------------------------------------------------

    def test_admin_can_change_member_role(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(
                self.agent_membership
            ),
            {
                "role":
                    OrganizationMembership.Role.ADMIN,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.agent_membership.refresh_from_db()

        self.assertEqual(
            self.agent_membership.role,
            OrganizationMembership.Role.ADMIN,
        )

    # ---------------------------------------------------------
    # Deactivation
    # ---------------------------------------------------------

    def test_deactivating_agent_unassigns_tickets(
        self,
    ):
        ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.customer,
            assigned_agent=self.agent,
            title="Assigned agent ticket",
            description="Test",
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(
                self.agent_membership
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.agent_membership.refresh_from_db()
        ticket.refresh_from_db()

        self.assertFalse(
            self.agent_membership.is_active
        )

        self.assertIsNone(
            ticket.assigned_agent
        )

        history_exists = (
            TicketHistory.objects
            .filter(
                ticket=ticket,
                changed_by=self.admin,
                action=(
                    TicketHistory.Action
                    .ASSIGNED_CHANGED
                ),
            )
            .exists()
        )

        self.assertTrue(
            history_exists
        )

    # ---------------------------------------------------------
    # Delete membership
    # ---------------------------------------------------------

    def test_admin_can_remove_agent_membership_without_deleting_user(
        self,
    ):
        user_id = self.agent.id

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.delete(
            self.detail_url(
                self.agent_membership
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            OrganizationMembership.objects
            .filter(
                pk=self.agent_membership.id,
            )
            .exists()
        )

        self.assertTrue(
            User.objects.filter(
                pk=user_id,
            ).exists()
        )

    # ---------------------------------------------------------
    # Last admin protection
    # ---------------------------------------------------------

    def test_last_admin_cannot_change_role(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(
                self.admin_membership
            ),
            {
                "role":
                    OrganizationMembership.Role.AGENT,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.admin_membership.refresh_from_db()

        self.assertEqual(
            self.admin_membership.role,
            OrganizationMembership.Role.ADMIN,
        )

    def test_last_admin_cannot_be_deactivated(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(
                self.admin_membership
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.admin_membership.refresh_from_db()

        self.assertTrue(
            self.admin_membership.is_active
        )

    def test_last_admin_cannot_be_deleted(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.delete(
            self.detail_url(
                self.admin_membership
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertTrue(
            OrganizationMembership.objects
            .filter(
                pk=self.admin_membership.id,
            )
            .exists()
        )

    # ---------------------------------------------------------
    # Tenant isolation
    # ---------------------------------------------------------

    def test_admin_cannot_manage_membership_from_other_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(
                self.other_admin_membership,
                organization=self.organization,
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.other_admin_membership.refresh_from_db()

        self.assertTrue(
            self.other_admin_membership.is_active
        )