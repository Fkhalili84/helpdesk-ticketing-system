from organizations.models import OrganizationMembership

from .models import Notification


def create_notification(
    *,
    organization,
    recipient,
    notification_type,
    title,
    message="",
    ticket=None,
    actor=None,
):
    if recipient is None:
        return None

    membership_exists = (
        OrganizationMembership.objects.filter(
            organization=organization,
            user=recipient,
            is_active=True,
        ).exists()
    )

    if not membership_exists:
        return None

    if (
        actor is not None
        and actor.pk == recipient.pk
    ):
        return None

    return Notification.objects.create(
        organization=organization,
        recipient=recipient,
        actor=actor,
        ticket=ticket,
        notification_type=notification_type,
        title=title,
        message=message,
    )