from django.utils import timezone
from rest_framework import serializers

from users.models import User

from .models import Ticket, TicketCategory, TicketMessage

class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = (
            "id",
            "name",
            "description",
        )


class TicketSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    customer_username = serializers.CharField(
        source="customer.username",
        read_only=True,
    )

    assigned_agent = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.AGENT,
            is_active=True,
        ),
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
            "customer",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return attrs

        user = request.user
        submitted_fields = set(self.initial_data.keys())

        if user.is_staff:
            return attrs

        if user.role == User.Role.CUSTOMER:
            forbidden_fields = {
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

        elif user.role == User.Role.AGENT:
            forbidden_fields = {
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
                        "Support agents cannot modify these fields: "
                        + ", ".join(sorted(invalid_fields))
                    )
                })

        return attrs

    def update(self, instance, validated_data):
        new_status = validated_data.get("status")

        if new_status == Ticket.Status.RESOLVED:
            if instance.resolved_at is None:
                instance.resolved_at = timezone.now()

        if new_status == Ticket.Status.CLOSED:
            if instance.closed_at is None:
                instance.closed_at = timezone.now()

        return super().update(instance, validated_data)
    

class TicketMessageSerializer(serializers.ModelSerializer):
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