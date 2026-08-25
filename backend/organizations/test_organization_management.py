from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Ticket
from users.models import User

from .models import (
    Organization,
    OrganizationMembership,
)


class OrganizationManagementTests(
    APITestCase
):

    def setUp(self):
        # -----------------------------------------------------
        # Organizations
        # -----------------------------------------------------

        self.organization = (
            Organization.objects.create(
                name="NexaCloud",
                slug="nexacloud",
                is_active=True,
            )
        )

        self.other_organization = (
            Organization.objects.create(
                name="Other Company",
                slug="other-organization",
                is_active=True,
            )
        )

        # -----------------------------------------------------
        # Users
        # -----------------------------------------------------

        self.admin = User.objects.create_user(
            username="organization_admin",
            password="Password123!",
        )

        self.agent = User.objects.create_user(
            username="organization_agent",
            password="Password123!",
        )

        self.customer = (
            User.objects.create_user(
                username="organization_customer",
                password="Password123!",
            )
        )

        self.inactive_agent = (
            User.objects.create_user(
                username="inactive_agent",
                password="Password123!",
            )
        )

        self.outside_user = (
            User.objects.create_user(
                username="outside_user",
                password="Password123!",
            )
        )

        # -----------------------------------------------------
        # Memberships
        # -----------------------------------------------------

        self.admin_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.admin,
                role=(
                    OrganizationMembership
                    .Role.ADMIN
                ),
                is_active=True,
            )
        )

        self.agent_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.agent,
                role=(
                    OrganizationMembership
                    .Role.AGENT
                ),
                is_active=True,
            )
        )

        self.customer_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.customer,
                role=(
                    OrganizationMembership
                    .Role.CUSTOMER
                ),
                is_active=True,
            )
        )

        self.inactive_membership = (
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.inactive_agent,
                role=(
                    OrganizationMembership
                    .Role.AGENT
                ),
                is_active=False,
            )
        )

        OrganizationMembership.objects.create(
            organization=(
                self.other_organization
            ),
            user=self.outside_user,
            role=(
                OrganizationMembership
                .Role.ADMIN
            ),
            is_active=True,
        )

        # -----------------------------------------------------
        # Tickets
        # -----------------------------------------------------

        self.ticket_1 = (
            Ticket.objects.create(
                organization=self.organization,
                customer=self.customer,
                title="Organization ticket 1",
                description="Test",
            )
        )

        self.ticket_2 = (
            Ticket.objects.create(
                organization=self.organization,
                customer=self.customer,
                title="Organization ticket 2",
                description="Test",
            )
        )

        Ticket.objects.create(
            organization=(
                self.other_organization
            ),
            customer=self.outside_user,
            title="Other organization ticket",
            description="Test",
        )

    def detail_url(
        self,
        organization=None,
    ):
        organization = (
            organization
            or self.organization
        )

        return reverse(
            "organization-management-detail",
            kwargs={
                "organization_slug":
                    organization.slug,
            },
        )

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def test_admin_can_view_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.organization.id,
        )

        self.assertEqual(
            response.data["name"],
            "NexaCloud",
        )

        self.assertEqual(
            response.data["slug"],
            "nexacloud",
        )

    def test_agent_can_view_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_customer_can_view_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def test_organization_statistics_are_correct(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        statistics = (
            response.data["statistics"]
        )

        self.assertEqual(
            statistics["member_count"],
            3,
        )

        self.assertEqual(
            statistics["admin_count"],
            1,
        )

        self.assertEqual(
            statistics["agent_count"],
            1,
        )

        self.assertEqual(
            statistics["customer_count"],
            1,
        )

        self.assertEqual(
            statistics[
                "inactive_member_count"
            ],
            1,
        )

        self.assertEqual(
            statistics["ticket_count"],
            2,
        )

    # ---------------------------------------------------------
    # PATCH
    # ---------------------------------------------------------

    def test_admin_can_update_organization_name(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(),
            {
                "name": "NexaCloud Support",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.name,
            "NexaCloud Support",
        )

        self.assertEqual(
            response.data["name"],
            "NexaCloud Support",
        )

    def test_agent_cannot_update_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.patch(
            self.detail_url(),
            {
                "name": "Hacked Company",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.name,
            "NexaCloud",
        )

    def test_customer_cannot_update_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.patch(
            self.detail_url(),
            {
                "name": "Customer Company",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.name,
            "NexaCloud",
        )

    # ---------------------------------------------------------
    # Protected fields
    # ---------------------------------------------------------

    def test_admin_cannot_change_organization_slug(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(),
            {
                "slug": "changed-slug",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.slug,
            "nexacloud",
        )

    def test_admin_cannot_change_organization_active_state(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.organization.refresh_from_db()

        self.assertTrue(
            self.organization.is_active
        )

    # ---------------------------------------------------------
    # Membership
    # ---------------------------------------------------------

    def test_user_without_membership_cannot_view_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.outside_user,
        )

        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_inactive_member_cannot_view_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.inactive_agent,
        )

        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ---------------------------------------------------------
    # Tenant isolation
    # ---------------------------------------------------------

    def test_admin_cannot_view_other_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.get(
            self.detail_url(
                self.other_organization
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_cannot_update_other_organization(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.patch(
            self.detail_url(
                self.other_organization
            ),
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.other_organization.refresh_from_db()

        self.assertEqual(
            self.other_organization.name,
            "Other Company",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_view_organization(
        self,
    ):
        response = self.client.get(
            self.detail_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )