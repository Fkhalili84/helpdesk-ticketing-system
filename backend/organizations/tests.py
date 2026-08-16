from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

from .models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
)


class CustomerRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.organization = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.register_url = reverse(
            "organization-customer-register",
            kwargs={
                "organization_slug": self.organization.slug,
            },
        )

    def test_customer_can_register_in_organization(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "new_customer",
                "email": "customer@nexacloud.test",
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get(
            username="new_customer",
        )

        self.assertEqual(
            user.email,
            "customer@nexacloud.test",
        )

        membership = OrganizationMembership.objects.get(
            user=user,
            organization=self.organization,
        )

        self.assertEqual(
            membership.role,
            OrganizationMembership.Role.CUSTOMER,
        )

        self.assertTrue(
            membership.is_active,
        )

    def test_registration_rejects_password_mismatch(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "new_customer",
                "email": "customer@nexacloud.test",
                "password": "StrongPassword123!",
                "password_confirm": "DifferentPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            User.objects.filter(
                username="new_customer",
            ).exists()
        )

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(
            username="existing_user",
            email="existing@nexacloud.test",
            password="StrongPassword123!",
        )

        response = self.client.post(
            self.register_url,
            {
                "username": "existing_user",
                "email": "different@nexacloud.test",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing_user",
            email="existing@nexacloud.test",
            password="StrongPassword123!",
        )

        response = self.client.post(
            self.register_url,
            {
                "username": "different_user",
                "email": "existing@nexacloud.test",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_registration_for_unknown_organization_returns_404(self):
        url = reverse(
            "organization-customer-register",
            kwargs={
                "organization_slug": "unknown-company",
            },
        )

        response = self.client.post(
            url,
            {
                "username": "new_customer",
                "email": "customer@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class OrganizationInvitationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.organization = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.other_organization = Organization.objects.create(
            name="ABC Company",
            slug="abc",
        )

        self.organization_admin = User.objects.create_user(
            username="org_admin",
            email="admin@nexacloud.test",
            password="StrongPassword123!",
        )

        self.agent = User.objects.create_user(
            username="existing_agent",
            email="agent@nexacloud.test",
            password="StrongPassword123!",
        )

        self.customer = User.objects.create_user(
            username="existing_customer",
            email="customer@nexacloud.test",
            password="StrongPassword123!",
        )

        self.other_admin = User.objects.create_user(
            username="other_admin",
            email="admin@abc.test",
            password="StrongPassword123!",
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.organization_admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.agent,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.customer,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.other_organization,
            user=self.other_admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

        self.invitation_url = reverse(
            "organization-invitation-list",
            kwargs={
                "organization_slug": self.organization.slug,
            },
        )

    def test_organization_admin_can_create_agent_invitation(self):
        self.client.force_authenticate(
            user=self.organization_admin,
        )

        response = self.client.post(
            self.invitation_url,
            {
                "email": "newagent@nexacloud.test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        invitation = OrganizationInvitation.objects.get(
            email="newagent@nexacloud.test",
        )

        self.assertEqual(
            invitation.organization,
            self.organization,
        )

        self.assertEqual(
            invitation.invited_by,
            self.organization_admin,
        )

        self.assertEqual(
            invitation.role,
            OrganizationMembership.Role.AGENT,
        )

        self.assertIsNotNone(
            invitation.expires_at,
        )

        self.assertIsNone(
            invitation.accepted_at,
        )

    def test_agent_cannot_create_invitation(self):
        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.post(
            self.invitation_url,
            {
                "email": "newagent@nexacloud.test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_customer_cannot_create_invitation(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.invitation_url,
            {
                "email": "newagent@nexacloud.test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_of_other_organization_cannot_create_invitation(self):
        self.client.force_authenticate(
            user=self.other_admin,
        )

        response = self.client.post(
            self.invitation_url,
            {
                "email": "newagent@nexacloud.test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_create_invitation(self):
        response = self.client.post(
            self.invitation_url,
            {
                "email": "newagent@nexacloud.test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_duplicate_pending_invitation_is_rejected(self):
        OrganizationInvitation.objects.create(
            organization=self.organization,
            email="duplicate@nexacloud.test",
            role=OrganizationMembership.Role.AGENT,
            invited_by=self.organization_admin,
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.client.force_authenticate(
            user=self.organization_admin,
        )

        response = self.client.post(
            self.invitation_url,
            {
                "email": "duplicate@nexacloud.test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_existing_member_cannot_be_invited_again(self):
        self.client.force_authenticate(
            user=self.organization_admin,
        )

        response = self.client.post(
            self.invitation_url,
            {
                "email": self.agent.email,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class InvitationAcceptanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.organization = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.admin = User.objects.create_user(
            username="org_admin",
            email="admin@nexacloud.test",
            password="StrongPassword123!",
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

        self.invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            email="newagent@nexacloud.test",
            role=OrganizationMembership.Role.AGENT,
            invited_by=self.admin,
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.detail_url = reverse(
            "invitation-detail",
            kwargs={
                "token": self.invitation.token,
            },
        )

        self.accept_url = reverse(
            "invitation-accept",
            kwargs={
                "token": self.invitation.token,
            },
        )

    def test_invitation_detail_is_public(self):
        response = self.client.get(
            self.detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.invitation.email,
        )

        self.assertEqual(
            response.data["status"],
            "pending",
        )

    def test_agent_can_accept_valid_invitation(self):
        response = self.client.post(
            self.accept_url,
            {
                "username": "new_agent",
                "first_name": "Reza",
                "last_name": "Ahmadi",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get(
            username="new_agent",
        )

        self.assertEqual(
            user.email,
            self.invitation.email,
        )

        membership = OrganizationMembership.objects.get(
            organization=self.organization,
            user=user,
        )

        self.assertEqual(
            membership.role,
            OrganizationMembership.Role.AGENT,
        )

        self.assertTrue(
            membership.is_active,
        )

        self.invitation.refresh_from_db()

        self.assertIsNotNone(
            self.invitation.accepted_at,
        )

    def test_invitation_cannot_be_accepted_twice(self):
        first_response = self.client.post(
            self.accept_url,
            {
                "username": "new_agent",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self.accept_url,
            {
                "username": "another_agent",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_expired_invitation_cannot_be_accepted(self):
        self.invitation.expires_at = (
            timezone.now()
            - timedelta(days=1)
        )

        self.invitation.save(
            update_fields=["expires_at"],
        )

        response = self.client.post(
            self.accept_url,
            {
                "username": "expired_agent",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            User.objects.filter(
                username="expired_agent",
            ).exists()
        )

    def test_password_mismatch_rejects_invitation_acceptance(self):
        response = self.client.post(
            self.accept_url,
            {
                "username": "new_agent",
                "password": "StrongPassword123!",
                "password_confirm": "DifferentPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            User.objects.filter(
                username="new_agent",
            ).exists()
        )