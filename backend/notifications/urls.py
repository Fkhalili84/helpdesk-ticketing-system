from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationReadAllView,
    NotificationUnreadCountView,
)


urlpatterns = [
    path(
        "organizations/"
        "<slug:organization_slug>/"
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),

    path(
        "organizations/"
        "<slug:organization_slug>/"
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),

    path(
        "organizations/"
        "<slug:organization_slug>/"
        "notifications/read-all/",
        NotificationReadAllView.as_view(),
        name="notification-read-all",
    ),

    path(
        "organizations/"
        "<slug:organization_slug>/"
        "notifications/"
        "<int:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
]