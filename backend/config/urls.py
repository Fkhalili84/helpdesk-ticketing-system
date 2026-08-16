from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/auth/",
        include("users.urls"),
    ),

    path(
        "api/organizations/",
        include("organizations.public_urls"),
    ),

    path(
        "api/organizations/<slug:organization_slug>/",
        include("organizations.urls"),
    ),

    path(
        "api/organizations/<slug:organization_slug>/",
        include("tickets.urls"),
    ),

    path(
        "api/invitations/",
        include("organizations.invitation_urls"),
    ),

    path(
        "api/",
        include("core.urls"),
    ),
]