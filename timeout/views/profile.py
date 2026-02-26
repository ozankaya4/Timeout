from django.utils import timezone
from datetime import timedelta
from timeout.models import Event


def get_profile_event(user):
    """Return the most relevant event: current → upcoming → recent."""
    now = timezone.now()
    two_hours = timedelta(hours=2)

    # on-going
    event = Event.objects.filter(
        creator=user,
        start_datetime__lte=now,
        end_datetime__gte=now,
    ).first()
    if event:
        return event, 'active'

    # will start soon
    event = Event.objects.filter(
        creator=user,
        start_datetime__gt=now,
        start_datetime__lte=now + two_hours,
    ).order_by('start_datetime').first()
    if event:
        return event, 'upcoming'

    # just ended
    event = Event.objects.filter(
        creator=user,
        end_datetime__lt=now,
        end_datetime__gte=now - two_hours,
    ).order_by('-end_datetime').first()
    if event:
        return event, 'recent'

    return None, None