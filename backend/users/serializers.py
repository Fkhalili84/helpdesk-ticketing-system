from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from organizations.models import OrganizationMembership


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        return User.objects.create_user(
            **validated_data,
        )


class MembershipSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(
        source="organization.id",
        read_only=True,
    )

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    organization_slug = serializers.CharField(
        source="organization.slug",
        read_only=True,
    )

    class Meta:
        model = OrganizationMembership
        fields = (
            "organization_id",
            "organization_name",
            "organization_slug",
            "role",
            "is_active",
            "joined_at",
        )


class UserSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "memberships",
        )

        read_only_fields = (
            "id",
            "username",
            "memberships",
        )

    def get_memberships(self, obj):
        memberships = (
            obj.organization_memberships
            .filter(is_active=True)
            .select_related("organization")
        )

        return MembershipSerializer(
            memberships,
            many=True,
        ).data