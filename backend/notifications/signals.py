from django.db.models.signals import (
    post_save,
    pre_save,
)
from django.dispatch import receiver

from organizations.models import OrganizationMembership
from tickets.models import (
    Ticket,
    TicketMessage,
)

from .models import Notification
from .services import create_notification


@receiver(
    pre_save,
    sender=Ticket,
    dispatch_uid="notification_ticket_pre_save",
)
def store_previous_ticket_state(
    sender,
    instance,
    **kwargs,
):
    instance._previous_assigned_agent_id = None
    instance._previous_status = None

    if not instance.pk:
        return

    try:
        previous_ticket = (
            Ticket.objects
            .only(
                "assigned_agent_id",
                "status",
            )
            .get(
                pk=instance.pk,
            )
        )
    except Ticket.DoesNotExist:
        return

    instance._previous_assigned_agent_id = (
        previous_ticket.assigned_agent_id
    )

    instance._previous_status = (
        previous_ticket.status
    )


@receiver(
    post_save,
    sender=Ticket,
    dispatch_uid="notification_ticket_post_save",
)
def create_ticket_notifications(
    sender,
    instance,
    created,
    **kwargs,
):
    previous_assigned_agent_id = getattr(
        instance,
        "_previous_assigned_agent_id",
        None,
    )

    previous_status = getattr(
        instance,
        "_previous_status",
        None,
    )

    # ---------------------------------------------------------
    # Ticket assignment
    # ---------------------------------------------------------

    assignment_changed = (
        instance.assigned_agent_id is not None
        and (
            created
            or previous_assigned_agent_id
            != instance.assigned_agent_id
        )
    )

    if assignment_changed:
        create_notification(
            organization=instance.organization,
            recipient=instance.assigned_agent,
            notification_type=(
                Notification.Type.TICKET_ASSIGNED
            ),
            title="Ticket assigned",
            message=(
                f'Ticket "{instance.title}" '
                "has been assigned to you."
            ),
            ticket=instance,
        )

    # ---------------------------------------------------------
    # Status change
    # ---------------------------------------------------------

    status_changed = (
        not created
        and previous_status is not None
        and previous_status != instance.status
    )

    if status_changed:
        create_notification(
            organization=instance.organization,
            recipient=instance.customer,
            notification_type=(
                Notification.Type.STATUS_CHANGED
            ),
            title="Ticket status changed",
            message=(
                f'Ticket "{instance.title}" '
                f"status changed to "
                f"{instance.get_status_display()}."
            ),
            ticket=instance,
        )


@receiver(
    post_save,
    sender=TicketMessage,
    dispatch_uid="notification_ticket_message_post_save",
)
def create_new_message_notification(
    sender,
    instance,
    created,
    **kwargs,
):
    if not created:
        return

    ticket = instance.ticket
    message_sender = instance.sender

    # ---------------------------------------------------------
    # Customer sent message
    # ---------------------------------------------------------

    if message_sender_id_equals(
        message_sender,
        ticket.customer_id,
    ):
        if ticket.assigned_agent_id is not None:
            create_notification(
                organization=ticket.organization,
                recipient=ticket.assigned_agent,
                actor=message_sender,
                notification_type=(
                    Notification.Type.NEW_MESSAGE
                ),
                title="New ticket message",
                message=(
                    f'New message on ticket '
                    f'"{ticket.title}".'
                ),
                ticket=ticket,
            )

        else:
            admin_memberships = (
                OrganizationMembership.objects
                .filter(
                    organization=ticket.organization,
                    role=(
                        OrganizationMembership.Role.ADMIN
                    ),
                    is_active=True,
                )
                .select_related("user")
            )

            for membership in admin_memberships:
                create_notification(
                    organization=ticket.organization,
                    recipient=membership.user,
                    actor=message_sender,
                    notification_type=(
                        Notification.Type.NEW_MESSAGE
                    ),
                    title="New ticket message",
                    message=(
                        f'New message on unassigned '
                        f'ticket "{ticket.title}".'
                    ),
                    ticket=ticket,
                )

        return

    # ---------------------------------------------------------
    # Agent/Admin sent message
    # ---------------------------------------------------------

    create_notification(
        organization=ticket.organization,
        recipient=ticket.customer,
        actor=message_sender,
        notification_type=(
            Notification.Type.NEW_MESSAGE
        ),
        title="New ticket message",
        message=(
            f'New message on ticket '
            f'"{ticket.title}".'
        ),
        ticket=ticket,
    )


def message_sender_id_equals(
    sender,
    user_id,
):
    return (
        sender is not None
        and sender.pk == user_id
    )