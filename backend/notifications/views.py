from django.shortcuts import get_object_or_404
from django.utils import timezone

from django_filters.rest_framework import (
    DjangoFilterBackend,
)


from organizations.models import (
    Organization,
    OrganizationMembership,
)

from .models import Notification
from .serializers import NotificationSerializer
from drf_spectacular.utils import extend_schema

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)

from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import (
    Organization,
    OrganizationMembership,
)

from .models import Notification
from .serializers import NotificationSerializer


class OrganizationNotificationMixin:
    def get_organization(self):
        if not hasattr(
            self,
            "_notification_organization",
        ):
            self._notification_organization = (
                get_object_or_404(
                    Organization,
                    slug=self.kwargs[
                        "organization_slug"
                    ],
                    is_active=True,
                )
            )

        return self._notification_organization

    def get_membership(self):
        organization = self.get_organization()

        membership = (
            OrganizationMembership.objects
            .filter(
                organization=organization,
                user=self.request.user,
                is_active=True,
            )
            .first()
        )

        if membership is None:
            raise PermissionDenied(
                "You are not a member of this organization."
            )

        return membership


@extend_schema_view(
    get=extend_schema(
        tags=["Notifications"],
        summary="List notifications",
        description=(
            "Returns notifications belonging to the "
            "authenticated user in the selected organization."
        ),
    ),
)
class NotificationListView(
    OrganizationNotificationMixin,
    generics.ListAPIView,
):
    serializer_class = NotificationSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]

    filterset_fields = [
        "is_read",
        "notification_type",
    ]

    ordering_fields = [
        "created_at",
    ]

    ordering = [
        "-created_at",
    ]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        self.get_membership()

        organization = self.get_organization()

        return (
            Notification.objects
            .filter(
                organization=organization,
                recipient=self.request.user,
            )
            .select_related(
                "actor",
                "ticket",
                "recipient",
                "organization",
            )
        )


class NotificationUnreadCountView(
    OrganizationNotificationMixin,
    APIView,
):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Notifications"],
        summary="Get unread notification count",
        description=(
            "Returns the number of unread notifications "
            "for the authenticated user."
        ),
        responses={
            200: inline_serializer(
                name="NotificationUnreadCountResponse",
                fields={
                    "unread_count": serializers.IntegerField(),
                },
            ),
        },
    )
    def get(
        self,
        request,
        organization_slug,
    ):
        self.get_membership()

        organization = self.get_organization()

        unread_count = (
            Notification.objects
            .filter(
                organization=organization,
                recipient=request.user,
                is_read=False,
            )
            .count()
        )

        return Response(
            {
                "unread_count": unread_count,
            }
        )


class NotificationMarkReadView(
    OrganizationNotificationMixin,
    APIView,
):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Notifications"],
        summary="Mark notification as read",
        description=(
            "Marks one notification belonging to the "
            "authenticated user as read."
        ),
        request=None,
        responses={
            200: NotificationSerializer,
        },
    )
    def patch(
        self,
        request,
        organization_slug,
        notification_id,
    ):
        self.get_membership()

        organization = self.get_organization()

        notification = get_object_or_404(
            Notification,
            pk=notification_id,
            organization=organization,
            recipient=request.user,
        )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()

            notification.save(
                update_fields=[
                    "is_read",
                    "read_at",
                ]
            )

        serializer = NotificationSerializer(
            notification
        )

        return Response(
            serializer.data
        )


class NotificationReadAllView(
    OrganizationNotificationMixin,
    APIView,
):
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        description=(
            "Marks all unread notifications belonging "
            "to the authenticated user as read."
        ),
        request=None,
        responses={
            200: inline_serializer(
                name="NotificationReadAllResponse",
                fields={
                    "updated": serializers.IntegerField(),
                },
            ),
        },
    )
    def post(
        self,
        request,
        organization_slug,
    ):
        self.get_membership()

        organization = self.get_organization()

        now = timezone.now()

        updated_count = (
            Notification.objects
            .filter(
                organization=organization,
                recipient=request.user,
                is_read=False,
            )
            .update(
                is_read=True,
                read_at=now,
            )
        )

        return Response(
            {
                "updated": updated_count,
            }
        )