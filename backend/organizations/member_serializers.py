from rest_framework import serializers

from .models import OrganizationMembership


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True,
    )

    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True,
    )

    class Meta:
        model = OrganizationMembership

        fields = [
            "id",
            "user_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
        ]

        read_only_fields = fields


class OrganizationMemberUpdateSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = OrganizationMembership

        fields = [
            "role",
            "is_active",
        ]