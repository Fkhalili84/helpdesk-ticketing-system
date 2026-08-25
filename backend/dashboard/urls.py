from django.urls import path

from .views import (
    DashboardPriorityView,
    DashboardSummaryView,
    DashboardAgentPerformanceView,
    DashboardResolutionMetricsView,
    DashboardSLAView,
)

urlpatterns = [
    path(
        "organizations/<slug:organization_slug>/dashboard/summary/",
        DashboardSummaryView.as_view(),
        name="dashboard-summary",
    ),
    path(
        "organizations/<slug:organization_slug>/dashboard/priorities/",
        DashboardPriorityView.as_view(),
        name="dashboard-priorities",
    ),
    path(
        "organizations/<slug:organization_slug>/dashboard/agents/",
        DashboardAgentPerformanceView.as_view(),
        name="dashboard-agents",
    ),
    path(
        "organizations/<slug:organization_slug>/dashboard/resolution/",
        DashboardResolutionMetricsView.as_view(),
        name="dashboard-resolution",
    ),
    path(
        "organizations/<slug:organization_slug>/dashboard/sla/",
        DashboardSLAView.as_view(),
        name="dashboard-sla",
    ),
]