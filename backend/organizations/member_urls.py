from django.urls import path

from .member_views import (
    OrganizationMemberDetailView,
    OrganizationMemberListView,
)


urlpatterns = [
    path(
        "organizations/"
        "<slug:organization_slug>/"
        "members/",
        OrganizationMemberListView.as_view(),
        name="organization-member-list",
    ),

    path(
        "organizations/"
        "<slug:organization_slug>/"
        "members/"
        "<int:membership_id>/",
        OrganizationMemberDetailView.as_view(),
        name="organization-member-detail",
    ),
]