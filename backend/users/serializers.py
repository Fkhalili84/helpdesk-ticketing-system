from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from rest_framework import serializers

from organizations.models import OrganizationMembership


User = get_user_model()


class CustomerRegisterSerializer(serializers.ModelSerializer):
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
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        )

    def validate_username(self, value):
        value = value.strip()

        if User.objects.filter(
            username__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )

        return value

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(
            email__iexact=email,
        ).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        organization = self.context["organization"]

        validated_data.pop("password_confirm")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get(
                "first_name",
                "",
            ),
            last_name=validated_data.get(
                "last_name",
                "",
            ),
            password=validated_data["password"],
        )

        OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=OrganizationMembership.Role.CUSTOMER,
            is_active=True,
        )

        return user


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