from django.utils import timezone
from rest_framework import serializers

from organizations.models import OrganizationMembership
from users.models import User

from .models import (
    Ticket,
    TicketCategory,
    TicketMessage,
)


class TicketCategorySerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta:
        model = TicketCategory

        fields = (
            "id",
            "name",
            "description",
            "organization",
            "organization_name",
        )

        read_only_fields = (
            "id",
            "organization",
            "organization_name",
        )


class TicketSerializer(serializers.ModelSerializer):
    ALLOWED_STATUS_TRANSITIONS = {
        Ticket.Status.OPEN: {
            Ticket.Status.IN_PROGRESS,
        },
        Ticket.Status.IN_PROGRESS: {
            Ticket.Status.RESOLVED,
        },
        Ticket.Status.RESOLVED: {
            Ticket.Status.CLOSED,
        },
        Ticket.Status.CLOSED: set(),
    }
    organization = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    customer = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    customer_username = serializers.CharField(
        source="customer.username",
        read_only=True,
    )

    assigned_agent = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),
        allow_null=True,
        required=False,
    )

    assigned_agent_username = serializers.CharField(
        source="assigned_agent.username",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Ticket

        fields = (
            "id",
            "organization",
            "organization_name",
            "title",
            "description",
            "customer",
            "customer_username",
            "assigned_agent",
            "assigned_agent_username",
            "category",
            "category_name",
            "priority",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        )

        read_only_fields = (
            "id",
            "organization",
            "customer",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        view = self.context.get("view")

        if view is None:
            return

        if not hasattr(view, "get_organization"):
            return

        view_kwargs = getattr(view, "kwargs", {})

        if "organization_slug" not in view_kwargs:
            return

        organization = view.get_organization()

        # Only active agents of the current organization
        # can be assigned to a ticket.
        self.fields["assigned_agent"].queryset = User.objects.filter(
            organization_memberships__organization=organization,
            organization_memberships__role=OrganizationMembership.Role.AGENT,
            organization_memberships__is_active=True,
            is_active=True,
        ).distinct()

        # A ticket can only use categories that belong
        # to the current organization.
        self.fields["category"].queryset = TicketCategory.objects.filter(
            organization=organization,
        )

    def validate_status_transition(self, attrs):
        if self.instance is None:
            return

        new_status = attrs.get("status")

        if new_status is None:
            return

        current_status = self.instance.status

        # Sending the current status again is harmless.
        if new_status == current_status:
            return

        allowed_statuses = self.ALLOWED_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            current_label = Ticket.Status(
                current_status
            ).label

            new_label = Ticket.Status(
                new_status
            ).label

            allowed_labels = [
                Ticket.Status(status_value).label
                for status_value in allowed_statuses
            ]

            if allowed_labels:
                allowed_text = ", ".join(
                    allowed_labels
                )
            else:
                allowed_text = "none"

            raise serializers.ValidationError({
                "status": (
                    f"Invalid status transition from "
                    f"'{current_label}' to '{new_label}'. "
                    f"Allowed next status: {allowed_text}."
                )
            })

    def validate(self, attrs):
        self.validate_status_transition(attrs)

        request = self.context.get("request")
        view = self.context.get("view")

        if (
            request is None
            or not request.user.is_authenticated
            or view is None
            or not hasattr(view, "get_organization")
        ):
            return attrs

        user = request.user

        # Django/platform admins are not restricted by
        # organization membership roles.
        if user.is_staff:
            return attrs

        organization = view.get_organization()

        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            is_active=True,
        ).first()

        if membership is None:
            raise serializers.ValidationError({
                "detail": "You are not a member of this organization."
            })

        submitted_fields = set(self.initial_data.keys())

        # Customers manage the content of their own tickets,
        # but operational fields belong to support staff.
        if membership.role == OrganizationMembership.Role.CUSTOMER:
            forbidden_fields = {
                "organization",
                "customer",
                "assigned_agent",
                "priority",
                "status",
                "resolved_at",
                "closed_at",
            }

            invalid_fields = submitted_fields & forbidden_fields

            if invalid_fields:
                raise serializers.ValidationError({
                    "detail": (
                        "Customers cannot modify these fields: "
                        + ", ".join(sorted(invalid_fields))
                    )
                })

        # Agents and organization admins manage operational fields,
        # but should not rewrite customer-created ticket content.
        elif membership.role in (
            OrganizationMembership.Role.AGENT,
            OrganizationMembership.Role.ADMIN,
        ):
            forbidden_fields = {
                "organization",
                "customer",
                "title",
                "description",
                "resolved_at",
                "closed_at",
            }

            invalid_fields = submitted_fields & forbidden_fields

            if invalid_fields:
                raise serializers.ValidationError({
                    "detail": (
                        "Organization staff cannot modify these fields: "
                        + ", ".join(sorted(invalid_fields))
                    )
                })

        return attrs

    def update(self, instance, validated_data):
        new_status = validated_data.get("status")
        current_status = instance.status

        status_changed = (
            new_status is not None
            and new_status != current_status
        )

        if status_changed:
            if new_status == Ticket.Status.RESOLVED:
                if instance.resolved_at is None:
                    instance.resolved_at = timezone.now()

            elif new_status == Ticket.Status.CLOSED:
                if instance.closed_at is None:
                    instance.closed_at = timezone.now()

        return super().update(
            instance,
            validated_data,
        )


class TicketMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True,
    )

    class Meta:
        model = TicketMessage

        fields = (
            "id",
            "ticket",
            "sender",
            "sender_username",
            "message",
            "created_at",
        )

        read_only_fields = (
            "id",
            "ticket",
            "sender",
            "created_at",
        )