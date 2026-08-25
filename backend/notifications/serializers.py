from rest_framework import serializers

from .models import Notification


class NotificationSerializer(
    serializers.ModelSerializer
):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Notification

        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "ticket",
            "actor_username",
            "is_read",
            "created_at",
            "read_at",
        ]

        read_only_fields = fields