from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


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
        "api/",
        include(
            "organizations.organization_urls"
        ),
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
    path(
        "api/",
        include("dashboard.urls"),
    ),
    path(
        "api/",
        include("notifications.urls"),
    ),
    path(
        "api/",
        include("organizations.member_urls"),
    ),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),
    
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema"
        ),
        name="redoc",
    ),
]