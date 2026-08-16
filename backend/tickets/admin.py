from django.contrib import admin

from .models import Ticket, TicketCategory, TicketMessage


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization", "created_at")
    search_fields = ("name",)
    list_filter = (
        "organization",
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "organization",
        "customer",
        "assigned_agent",
        "category",
        "priority",
        "status",
        "created_at",
    )

    list_filter = (
        "organization",
        "status",
        "priority",
        "category",
    )

    search_fields = (
        "title",
        "description",
        "customer__username",
        "assigned_agent__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
    )


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket",
        "sender",
        "created_at",
    )

    search_fields = (
        "message",
        "sender__username",
        "ticket__title",
    )

    readonly_fields = ("created_at",)