from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from .models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
)

User = get_user_model()


class OrganizationOnboardingSerializer(serializers.Serializer):
    organization_name = serializers.CharField(
        max_length=150,
    )

    organization_slug = serializers.SlugField(
        max_length=160,
    )

    username = serializers.CharField(
        max_length=150,
    )

    email = serializers.EmailField()

    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True,
    )

    def validate_organization_slug(self, value):
        value = value.strip().lower()

        if Organization.objects.filter(
            slug__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                "An organization with this slug already exists."
            )

        return value

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
        validated_data.pop("password_confirm")

        organization_name = validated_data.pop(
            "organization_name"
        )

        organization_slug = validated_data.pop(
            "organization_slug"
        )

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

        organization = Organization.objects.create(
            name=organization_name,
            slug=organization_slug,
            created_by=user,
            is_active=True,
        )

        OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

        return {
            "user": user,
            "organization": organization,
        }

class OrganizationInvitationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    organization_slug = serializers.CharField(
        source="organization.slug",
        read_only=True,
    )

    invited_by_username = serializers.CharField(
        source="invited_by.username",
        read_only=True,
    )

    status = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationInvitation

        fields = (
            "id",
            "email",
            "role",
            "organization_name",
            "organization_slug",
            "invited_by_username",
            "token",
            "expires_at",
            "accepted_at",
            "created_at",
            "status",
        )

        read_only_fields = (
            "id",
            "role",
            "organization_name",
            "organization_slug",
            "invited_by_username",
            "token",
            "expires_at",
            "accepted_at",
            "created_at",
            "status",
        )

    def get_status(self, obj):
        if obj.accepted_at:
            return "accepted"

        if (
            obj.expires_at
            and obj.expires_at <= timezone.now()
        ):
            return "expired"

        return "pending"

    def validate_email(self, value):
        email = value.strip().lower()

        organization = self.context.get("organization")

        if organization is None:
            return email

        existing_member = OrganizationMembership.objects.filter(
            organization=organization,
            user__email__iexact=email,
            is_active=True,
        ).exists()

        if existing_member:
            raise serializers.ValidationError(
                "This user is already a member of the organization."
            )

        pending_invitation = OrganizationInvitation.objects.filter(
            organization=organization,
            email__iexact=email,
            accepted_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).exists()

        if pending_invitation:
            raise serializers.ValidationError(
                "An active invitation already exists for this email."
            )

        return email


class InvitationAcceptSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
    )

    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True,
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

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        invitation = self.context["invitation"]

        if invitation.accepted_at:
            raise serializers.ValidationError({
                "detail": "This invitation has already been accepted."
            })

        if (
            invitation.expires_at
            and invitation.expires_at <= timezone.now()
        ):
            raise serializers.ValidationError({
                "detail": "This invitation has expired."
            })

        if User.objects.filter(
            email__iexact=invitation.email,
        ).exists():
            raise serializers.ValidationError({
                "email": (
                    "An account with this email already exists."
                )
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        invitation = OrganizationInvitation.objects.select_for_update().get(
            pk=self.context["invitation"].pk,
        )

        # Check again after locking the invitation row.
        if invitation.accepted_at:
            raise serializers.ValidationError({
                "detail": "This invitation has already been accepted."
            })

        if (
            invitation.expires_at
            and invitation.expires_at <= timezone.now()
        ):
            raise serializers.ValidationError({
                "detail": "This invitation has expired."
            })

        validated_data.pop("password_confirm")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=invitation.email,
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
            organization=invitation.organization,
            user=user,
            role=invitation.role,
            is_active=True,
        )

        invitation.accepted_at = timezone.now()

        invitation.save(
            update_fields=[
                "accepted_at",
            ],
        )

        return user