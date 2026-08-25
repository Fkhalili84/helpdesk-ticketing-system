from django.db.models import Count, Q

from rest_framework import serializers

from tickets.models import Ticket

from .models import (
    Organization,
    OrganizationMembership,
)


class OrganizationDetailSerializer(
    serializers.ModelSerializer
):
    statistics = serializers.SerializerMethodField()

    class Meta:
        model = Organization

        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "statistics",
        ]

        read_only_fields = fields

    def get_statistics(
        self,
        organization,
    ):
        membership_statistics = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                is_active=True,
            )
            .aggregate(
                member_count=Count("id"),

                admin_count=Count(
                    "id",
                    filter=Q(
                        role=(
                            OrganizationMembership
                            .Role.ADMIN
                        )
                    ),
                ),

                agent_count=Count(
                    "id",
                    filter=Q(
                        role=(
                            OrganizationMembership
                            .Role.AGENT
                        )
                    ),
                ),

                customer_count=Count(
                    "id",
                    filter=Q(
                        role=(
                            OrganizationMembership
                            .Role.CUSTOMER
                        )
                    ),
                ),
            )
        )

        inactive_member_count = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                is_active=False,
            )
            .count()
        )

        ticket_count = (
            Ticket.objects
            .filter(
                organization=organization,
            )
            .count()
        )

        return {
            "member_count": (
                membership_statistics[
                    "member_count"
                ]
            ),

            "admin_count": (
                membership_statistics[
                    "admin_count"
                ]
            ),

            "agent_count": (
                membership_statistics[
                    "agent_count"
                ]
            ),

            "customer_count": (
                membership_statistics[
                    "customer_count"
                ]
            ),

            "inactive_member_count":
                inactive_member_count,

            "ticket_count":
                ticket_count,
        }


class OrganizationUpdateSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Organization

        fields = [
            "name",
        ]

    def validate(
        self,
        attrs,
    ):
        allowed_fields = {
            "name",
        }

        submitted_fields = set(
            self.initial_data.keys()
        )

        unsupported_fields = (
            submitted_fields
            - allowed_fields
        )

        if unsupported_fields:
            errors = {
                field: (
                    "This field cannot be modified."
                )
                for field in unsupported_fields
            }

            raise serializers.ValidationError(
                errors
            )

        return attrs