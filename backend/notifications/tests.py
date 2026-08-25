from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import (
    Organization,
    OrganizationMembership,
)

from tickets.models import (
    Ticket,
    TicketMessage,
)

from users.models import User

from .models import Notification


class NotificationAPITests(APITestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="NexaCloud",
            slug="nexacloud",
        )

        self.other_organization = (
            Organization.objects.create(
                name="Other Company",
                slug="other-company-notifications",
            )
        )

        self.customer = User.objects.create_user(
            username="notification_customer",
            password="Password123!",
        )

        self.agent = User.objects.create_user(
            username="notification_agent",
            password="Password123!",
        )

        self.admin = User.objects.create_user(
            username="notification_admin",
            password="Password123!",
        )

        self.outside_user = User.objects.create_user(
            username="notification_outside",
            password="Password123!",
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.customer,
            role=OrganizationMembership.Role.CUSTOMER,
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
            user=self.admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=self.other_organization,
            user=self.outside_user,
            role=OrganizationMembership.Role.AGENT,
            is_active=True,
        )

        self.ticket = Ticket.objects.create(
            organization=self.organization,
            customer=self.customer,
            title="Notification test ticket",
            description="Test",
            status=Ticket.Status.OPEN,
        )

        # Assign without triggering model save signals.
        Ticket.objects.filter(
            pk=self.ticket.pk,
        ).update(
            assigned_agent_id=self.agent.id,
        )

        self.ticket.refresh_from_db()

        Notification.objects.all().delete()

    def list_url(self):
        return reverse(
            "notification-list",
            kwargs={
                "organization_slug":
                    self.organization.slug,
            },
        )

    def unread_count_url(self):
        return reverse(
            "notification-unread-count",
            kwargs={
                "organization_slug":
                    self.organization.slug,
            },
        )

    def read_all_url(self):
        return reverse(
            "notification-read-all",
            kwargs={
                "organization_slug":
                    self.organization.slug,
            },
        )

    def mark_read_url(
        self,
        notification,
    ):
        return reverse(
            "notification-mark-read",
            kwargs={
                "organization_slug":
                    self.organization.slug,
                "notification_id":
                    notification.id,
            },
        )

    # ---------------------------------------------------------
    # Automatic notifications
    # ---------------------------------------------------------

    def test_ticket_assignment_creates_notification(self):
        Ticket.objects.filter(
            pk=self.ticket.pk,
        ).update(
            assigned_agent=None,
        )

        self.ticket.refresh_from_db()

        Notification.objects.all().delete()

        self.ticket.assigned_agent = self.agent

        self.ticket.save(
            update_fields=[
                "assigned_agent",
            ]
        )

        notification = Notification.objects.get(
            recipient=self.agent,
            notification_type=(
                Notification.Type.TICKET_ASSIGNED
            ),
        )

        self.assertEqual(
            notification.organization,
            self.organization,
        )

        self.assertEqual(
            notification.ticket,
            self.ticket,
        )

        self.assertFalse(
            notification.is_read
        )

    def test_status_change_notifies_customer(self):
        self.ticket.status = (
            Ticket.Status.IN_PROGRESS
        )

        self.ticket.save(
            update_fields=[
                "status",
            ]
        )

        notification = Notification.objects.get(
            recipient=self.customer,
            notification_type=(
                Notification.Type.STATUS_CHANGED
            ),
        )

        self.assertEqual(
            notification.ticket,
            self.ticket,
        )

        self.assertFalse(
            notification.is_read
        )

    def test_customer_message_notifies_assigned_agent(self):
        TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.customer,
            message="I have more information.",
        )

        notification = Notification.objects.get(
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
        )

        self.assertEqual(
            notification.actor,
            self.customer,
        )

        self.assertEqual(
            notification.ticket,
            self.ticket,
        )

    def test_agent_message_notifies_customer(self):
        TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.agent,
            message="I am checking the problem.",
        )

        notification = Notification.objects.get(
            recipient=self.customer,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
        )

        self.assertEqual(
            notification.actor,
            self.agent,
        )

        self.assertEqual(
            notification.ticket,
            self.ticket,
        )

    # ---------------------------------------------------------
    # Notification list
    # ---------------------------------------------------------

    def test_user_only_sees_own_notifications(self):
        own_notification = Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Agent notification",
            message="Test",
            ticket=self.ticket,
        )

        Notification.objects.create(
            organization=self.organization,
            recipient=self.customer,
            notification_type=(
                Notification.Type.STATUS_CHANGED
            ),
            title="Customer notification",
            message="Test",
            ticket=self.ticket,
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                own_notification.id,
            },
        )

    # ---------------------------------------------------------
    # Unread count
    # ---------------------------------------------------------

    def test_unread_count(self):
        Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Unread 1",
        )

        Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Unread 2",
        )

        Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Already read",
            is_read=True,
            read_at=timezone.now(),
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.get(
            self.unread_count_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["unread_count"],
            2,
        )

    # ---------------------------------------------------------
    # Mark read
    # ---------------------------------------------------------

    def test_user_can_mark_notification_as_read(self):
        notification = Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Unread notification",
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.patch(
            self.mark_read_url(
                notification
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read
        )

        self.assertIsNotNone(
            notification.read_at
        )

    def test_user_cannot_mark_other_users_notification_as_read(
        self,
    ):
        notification = Notification.objects.create(
            organization=self.organization,
            recipient=self.customer,
            notification_type=(
                Notification.Type.STATUS_CHANGED
            ),
            title="Customer only",
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.patch(
            self.mark_read_url(
                notification
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # Read all
    # ---------------------------------------------------------

    def test_user_can_mark_all_notifications_as_read(self):
        Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Notification 1",
        )

        Notification.objects.create(
            organization=self.organization,
            recipient=self.agent,
            notification_type=(
                Notification.Type.NEW_MESSAGE
            ),
            title="Notification 2",
        )

        self.client.force_authenticate(
            user=self.agent,
        )

        response = self.client.post(
            self.read_all_url(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["updated"],
            2,
        )

        unread_exists = (
            Notification.objects
            .filter(
                organization=self.organization,
                recipient=self.agent,
                is_read=False,
            )
            .exists()
        )

        self.assertFalse(
            unread_exists
        )

    # ---------------------------------------------------------
    # Tenant isolation
    # ---------------------------------------------------------

    def test_other_organization_user_cannot_view_notifications(
        self,
    ):
        self.client.force_authenticate(
            user=self.outside_user,
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_view_notifications(self):
        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )