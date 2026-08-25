from django.conf import settings
from django.db import models


class Notification(models.Model):

    class Type(models.TextChoices):
        TICKET_ASSIGNED = (
            "ticket_assigned",
            "Ticket Assigned",
        )
        STATUS_CHANGED = (
            "status_changed",
            "Status Changed",
        )
        NEW_MESSAGE = (
            "new_message",
            "New Message",
        )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_notifications",
    )

    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=50,
        choices=Type.choices,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField(
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "recipient",
                    "created_at",
                ],
                name="notif_org_user_created_idx",
            ),
            models.Index(
                fields=[
                    "recipient",
                    "is_read",
                ],
                name="notif_user_read_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.recipient.username} - "
            f"{self.get_notification_type_display()}"
        )