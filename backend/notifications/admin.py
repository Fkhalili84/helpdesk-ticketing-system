from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "recipient",
        "organization",
        "notification_type",
        "ticket",
        "is_read",
        "created_at",
    ]

    list_filter = [
        "notification_type",
        "is_read",
        "organization",
    ]

    search_fields = [
        "recipient__username",
        "title",
        "message",
    ]

    readonly_fields = [
        "created_at",
        "read_at",
    ]