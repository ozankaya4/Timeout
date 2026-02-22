from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from timeout.models import Event


def get_user_events(user):
    """Return all events belonging to the given user."""
    return Event.objects.filter(creator=user)


def count_by_type(events):
    """Return a dict mapping each event type label to its count."""
    counts = {label: 0 for _, label in Event.EventType.choices}
    for event in events:
        label = Event.EventType(event.event_type).label
        counts[label] += 1
    return counts


def events_last_n_weeks(events, n=8):
    """Return weekly event counts for the last n weeks, oldest first."""
    now = timezone.now()
    weeks = []
    for i in range(n - 1, -1, -1):
        week_start = now - timezone.timedelta(weeks=i + 1)
        week_end = now - timezone.timedelta(weeks=i)
        label = week_start.strftime('%d %b')
        count = events.filter(
            start_datetime__gte=week_start,
            start_datetime__lt=week_end,
        ).count()
        weeks.append({'label': label, 'count': count})
    return weeks


def events_last_n_months(events, n=6):
    """Return monthly event counts for the last n months, oldest first."""
    now = timezone.now()
    months = []
    for i in range(n - 1, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year = now.year - ((now.month - i - 1) // 12)
        label = timezone.datetime(year, month, 1).strftime('%b %Y')
        count = events.filter(
            start_datetime__year=year,
            start_datetime__month=month,
        ).count()
        months.append({'label': label, 'count': count})
    return months


def upcoming_urgent_count(events):
    """Return the count of deadlines and exams in the next 7 days."""
    now = timezone.now()
    soon = now + timezone.timedelta(days=7)
    urgent_types = [Event.EventType.DEADLINE, Event.EventType.EXAM]
    return events.filter(
        event_type__in=urgent_types,
        start_datetime__gte=now,
        start_datetime__lte=soon,
    ).count()


def build_context(user):
    """Assemble all statistics data into a context dict."""
    events = get_user_events(user)
    return {
        'total_events': events.count(),
        'type_counts': count_by_type(events),
        'weekly_data': events_last_n_weeks(events),
        'monthly_data': events_last_n_months(events),
        'urgent_count': upcoming_urgent_count(events),
    }


@login_required
def statistics_view(request):
    """Render the statistics page for the logged-in user."""
    context = build_context(request.user)
    return render(request, 'timeout/statistics.html', context)