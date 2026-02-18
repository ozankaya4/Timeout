from .models import Event
from django.shortcuts import get_object_or_404, render

def event_details(request, event_id):
    """View to display details of a specific event."""
    event = get_object_or_404(Event, id=event_id)
    context = {
        'event': event,
        'is_past': event.is_past,
        'is_ongoing': event.is_ongoing,
        'is_upcoming': event.is_upcoming
    }
    return render(request, 'timeout/event_details.html', context)