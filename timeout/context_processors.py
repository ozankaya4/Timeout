from timeout.views.ai_suggestions import get_ai_suggestions
from datetime import date
from timeout.models import Event

def ai_suggestions(request):
    if not request.user.is_authenticated:
        return {"ai_suggestions": []}

    # Get today's events for this user
    events_today = Event.objects.filter(
        creator=request.user,
        start_datetime__date=date.today()
    ).order_by('start_datetime')

    suggestions = get_ai_suggestions(request.user, events_today)
    return {"ai_suggestions": suggestions}