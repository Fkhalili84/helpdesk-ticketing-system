from django.urls import path

from .views import (
    CustomerRegisterView,
    OrganizationInvitationListCreateView,
)


urlpatterns = [
    path(
        "register/",
        CustomerRegisterView.as_view(),
        name="organization-customer-register",
    ),

    path(
        "invitations/",
        OrganizationInvitationListCreateView.as_view(),
        name="organization-invitation-list",
    ),
]