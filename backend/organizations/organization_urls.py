from django.urls import path

from .organization_views import (
    OrganizationDetailView,
)


urlpatterns = [
    path(
        "organizations/"
        "<slug:organization_slug>/",
        OrganizationDetailView.as_view(),
        name="organization-management-detail",
    ),
]