from django.utils import timezone
from timeout.models import Event


class DeadlineService:
    """Service to help for deadline list view
    Provides calculations for time remainig, time elapsed and urgency for the deadlines
    Gets them in a human readabke format from time delta function"""

    @staticmethod
    def get_active_deadlines(user):
        """Gets all active deadline events for a user, sorted by upcoming first."""
        if not user.is_authenticated:
            return []
        deadlines = Event.objects.filter(
            creator=user,
            event_type=Event.EventType.DEADLINE,
            is_completed=False,
        ).order_by('start_datetime')
        return _enrich_events(deadlines)

    @staticmethod
    def get_filtered_deadlines(user, status_filter='active', sort_order='asc', event_type=None):
        """Get deadlines with filtering and sorting.
        Allows user to filter by active/completed/all and by event types.
        Also allows to sort from old to new or new to old."""
        if not user.is_authenticated:
            return []
        qs = DeadlineService._apply_filters(user, status_filter, sort_order, event_type)
        return _enrich_events(qs, include_completed=True)

    @staticmethod
    def _apply_filters(user, status_filter, sort_order, event_type):
        """Build filtered and sorted queryset for deadline list."""
        qs = Event.objects.filter(creator=user)
        if event_type:
            qs = qs.filter(event_type=event_type)
        if status_filter == 'active':
            qs = qs.filter(is_completed=False)
        elif status_filter == 'completed':
            qs = qs.filter(is_completed=True)
        ordering = 'end_datetime' if sort_order == 'asc' else '-end_datetime'
        return qs.order_by(ordering)

    @staticmethod
    def mark_complete(user, event_id):
        """Mark event as completed."""
        try:
            event = Event.objects.get(
                pk=event_id,
                creator=user,
                is_completed=False,
            )
            event.is_completed = True
            event.save(update_fields=['is_completed', 'updated_at'])
            return event
        except Event.DoesNotExist:
            return None

    @staticmethod
    def get_all_active_events(user):
        """Return all non-completed, non-cancelled user events grouped by type."""
        if not user.is_authenticated:
            return {}
        now = timezone.now()
        qs = DeadlineService._active_events_query(user, now)
        events_by_type = {}
        for event in qs:
            item = _build_event_item(event, now)
            events_by_type.setdefault(event.event_type, []).append(item)
        return events_by_type

    @staticmethod
    def _active_events_query(user, now):
        """Build queryset for all active non-cancelled events."""
        from django.db.models import Q
        return Event.objects.filter(
            creator=user,
            is_completed=False,
        ).exclude(status=Event.EventStatus.CANCELLED).filter(
            Q(event_type=Event.EventType.DEADLINE) |
            Q(event_type=Event.EventType.STUDY_SESSION) |
            Q(event_type__in=[
                Event.EventType.EXAM,
                Event.EventType.CLASS,
                Event.EventType.MEETING,
                Event.EventType.OTHER,
            ], end_datetime__gte=now)
        ).order_by('start_datetime')


def _enrich_events(qs, include_completed=False):
    """Build enriched event dicts with urgency and time displays."""
    now = timezone.now()
    results = []
    for event in qs:
        time_remaining = event.end_datetime - now
        time_elapsed = now - event.created_at
        remaining_seconds = time_remaining.total_seconds()
        urgency = _compute_deadline_urgency(event, remaining_seconds, include_completed)
        results.append({
            'event': event,
            'urgency_status': urgency,
            'time_remaining': time_remaining,
            'time_remaining_display': _format_timedelta(time_remaining),
            'time_elapsed_display': _format_elapsed(time_elapsed),
        })
    return results


def _compute_deadline_urgency(event, remaining_seconds, include_completed=False):
    """Determine urgency status for a deadline event."""
    if include_completed and event.is_completed:
        return 'completed'
    if remaining_seconds < 0:
        return 'overdue'
    if remaining_seconds <= 86400:
        return 'urgent'
    return 'normal'


def _build_event_item(event, now):
    """Build enriched dict for a single event with urgency and time displays."""
    time_remaining = event.end_datetime - now
    time_elapsed = now - event.created_at
    remaining_seconds = time_remaining.total_seconds()
    if event.event_type == Event.EventType.DEADLINE:
        if remaining_seconds < 0:
            urgency_status = 'overdue'
        elif remaining_seconds <= 86400:
            urgency_status = 'urgent'
        else:
            urgency_status = 'normal'
    else:
        urgency_status = 'missed' if remaining_seconds < 0 else 'upcoming'
    return {
        'event': event,
        'urgency_status': urgency_status,
        'time_remaining': time_remaining,
        'time_remaining_display': _format_timedelta(time_remaining),
        'time_elapsed_display': _format_elapsed(time_elapsed),
    }


def _format_timedelta(td):
    """Calculation for time left.
    Formatting to make it human readable for how much time has left in terms of days and hours"""
    total_seconds = int(td.total_seconds())

    # Python calculations to show if an event is overdue, and show how much time passed
    if total_seconds < 0:
        total_seconds = abs(total_seconds)
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = remainder // 60
        if days > 0:
            return f"{days}d {hours}h overdue"
        if hours > 0:
            return f"{hours}h {minutes}m overdue"
        return f"{minutes}m overdue"

    # If not overdue calculate how much time is left
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days > 0:
        return f"{days}d {hours}h left"
    if hours > 0:
        return f"{hours}h {minutes}m left"
    return f"{minutes}m left"


def _format_elapsed(td):
    """Calculation for time passed since creation as 'Added x ago'.
    Same as before formatting to make it human readable on the page"""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "Added just now"

    days = total_seconds // 86400  # 86400 seconds in one day
    if days > 0:
        return f"Added {days} day{'s' if days != 1 else ''} ago"

    hours = total_seconds // 3600  # 3600 seconds in one hour
    if hours > 0:
        return f"Added {hours} hour{'s' if hours != 1 else ''} ago"

    minutes = total_seconds // 60
    if minutes > 0:
        return f"Added {minutes} min ago"

    return "Added just now"
