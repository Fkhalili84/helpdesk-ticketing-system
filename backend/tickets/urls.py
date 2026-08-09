from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    TicketCategoryViewSet,
    TicketMessageListCreateView,
    TicketViewSet,
)


router = SimpleRouter()

router.register(
    "tickets",
    TicketViewSet,
    basename="ticket",
)

router.register(
    "ticket-categories",
    TicketCategoryViewSet,
    basename="ticket-category",
)


urlpatterns = [
    path(
        "tickets/<int:ticket_id>/messages/",
        TicketMessageListCreateView.as_view(),
        name="ticket-message-list",
    ),
]

urlpatterns += router.urls