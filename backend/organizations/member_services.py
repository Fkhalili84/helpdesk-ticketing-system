from rest_framework.exceptions import ValidationError

from tickets.models import (
    Ticket,
    TicketHistory,
)

from .models import OrganizationMembership


def ensure_admin_continuity(
    *,
    membership,
    final_role,
    final_is_active,
):
    """
    Prevent an organization from being left without
    any active ADMIN membership.
    """

    currently_active_admin = (
        membership.role
        == OrganizationMembership.Role.ADMIN
        and membership.is_active
    )

    will_remain_active_admin = (
        final_role
        == OrganizationMembership.Role.ADMIN
        and final_is_active
    )

    if (
        not currently_active_admin
        or will_remain_active_admin
    ):
        return

    another_admin_exists = (
        OrganizationMembership.objects
        .select_for_update()
        .filter(
            organization=membership.organization,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )
        .exclude(
            pk=membership.pk,
        )
        .exists()
    )

    if not another_admin_exists:
        raise ValidationError(
            {
                "detail": (
                    "The last active organization admin "
                    "cannot be removed, deactivated, "
                    "or changed to another role."
                )
            }
        )


def unassign_member_tickets(
    *,
    organization,
    user,
    changed_by,
):
    """
    Unassign tickets from a member who can no longer
    act as an organization staff member.

    The change is also recorded in TicketHistory.
    """

    tickets = (
        Ticket.objects
        .select_for_update()
        .filter(
            organization=organization,
            assigned_agent=user,
        )
        .select_related(
            "assigned_agent",
        )
    )

    updated_count = 0

    for ticket in tickets:
        old_value = user.username

        ticket.assigned_agent = None

        ticket.save(
            update_fields=[
                "assigned_agent",
                "updated_at",
            ]
        )

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=changed_by,
            action=TicketHistory.Action.ASSIGNED_CHANGED,
            old_value=old_value,
            new_value="",
        )

        updated_count += 1

    return updated_count
