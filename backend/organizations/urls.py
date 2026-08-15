from django.urls import path

from .views import (
    OrganizationInvitationListCreateView,
)


urlpatterns = [
    path(
        "invitations/",
        OrganizationInvitationListCreateView.as_view(),
        name="organization-invitation-list",
    ),
]