from django.urls import path

from .views import OrganizationOnboardingView


urlpatterns = [
    path(
        "onboard/",
        OrganizationOnboardingView.as_view(),
        name="organization-onboarding",
    ),
]