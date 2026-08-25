from tickets.models import Ticket


SLA_RESOLUTION_HOURS = {
    Ticket.Priority.URGENT: 2,
    Ticket.Priority.HIGH: 8,
    Ticket.Priority.MEDIUM: 24,
    Ticket.Priority.LOW: 48,
}