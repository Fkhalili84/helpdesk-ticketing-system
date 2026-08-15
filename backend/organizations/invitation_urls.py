from django.urls import path

from .views import (
    InvitationAcceptView,
    InvitationDetailView,
)


urlpatterns = [
    path(
        "<uuid:token>/",
        InvitationDetailView.as_view(),
        name="invitation-detail",
    ),

    path(
        "<uuid:token>/accept/",
        InvitationAcceptView.as_view(),
        name="invitation-accept",
    ),
]