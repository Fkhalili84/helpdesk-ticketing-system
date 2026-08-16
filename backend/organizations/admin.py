from django.contrib import admin

from .models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "slug",
    )

    list_filter = (
        "is_active",
    )


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "organization",
        "role",
        "is_active",
        "joined_at",
    )

    list_filter = (
        "role",
        "is_active",
        "organization",
    )

    search_fields = (
        "user__username",
        "user__email",
        "organization__name",
    )


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "organization",
        "role",
        "invited_by",
        "created_at",
        "accepted_at",
    )

    list_filter = (
        "role",
        "organization",
    )

    search_fields = (
        "email",
        "organization__name",
    )

    readonly_fields = (
        "token",
        "created_at",
        "accepted_at",
    )