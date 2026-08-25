from django.shortcuts import get_object_or_404
from django.utils import timezone

from django_filters.rest_framework import (
    DjangoFilterBackend,
)

from rest_framework import generics
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
        return get_object_or_404(
            Organization,
            slug=self.kwargs["organization_slug"],
            is_active=True,
        )

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