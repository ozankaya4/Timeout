"""
Utility functions for Timeout views and services.
"""
from datetime import datetime, date
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

AI_DISABLED_MESSAGE = 'AI features are disabled on this demo deployment.'
DEMO_USERNAME = 'demo'


def ai_features_enabled():
    """Return True if an OpenAI API key is configured."""
    return bool(getattr(settings, 'OPENAI_API_KEY', ''))


def ai_disabled_response():
    """Return the JSON response AI endpoints send when no API key is configured."""
    return JsonResponse({'success': False, 'ai_disabled': True, 'error': AI_DISABLED_MESSAGE})


def is_demo_account(user):
    """Return True for the shared demo login, whose credentials are public."""
    return user.username == DEMO_USERNAME


def parse_aware_dt(dt_str):
    """Convert an ISO-format string to a timezone-aware datetime."""
    return timezone.make_aware(datetime.fromisoformat(dt_str))


def ai_cache_key(kind, user_id):
    """Build a daily per-user cache key for AI features."""
    return f"ai_{kind}_{user_id}_{date.today()}"


def urgency_label(event, time_remaining):
    """Determine the urgency label for an event."""
    if event.is_completed:
        return 'completed'
    remaining_seconds = time_remaining.total_seconds()
    if remaining_seconds < 0:
        return 'overdue'
    if remaining_seconds <= 86400:
        return 'urgent'
    return 'normal'


def time_string(td):
    """Human-readable string for time remaining or overdue."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return _overdue_time(abs(total_seconds))
    return _remaining_time(total_seconds)


def _overdue_time(total_seconds):
    """Format a positive seconds value as 'Xd Yh overdue'."""
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days > 0:
        return f"{days}d {hours}h overdue"
    if hours > 0:
        return f"{hours}h {minutes}m overdue"
    return f"{minutes}m overdue"


def _remaining_time(total_seconds):
    """Format a positive seconds value as 'Xd Yh left'."""
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days > 0:
        return f"{days}d {hours}h left"
    if hours > 0:
        return f"{hours}h {minutes}m left"
    return f"{minutes}m left"


def time_passed(td):
    """Format elapsed time since creation as 'Added X ago'."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "Added just now"
    days = total_seconds // 86400
    if days > 0:
        return f"Added {days} day{'s' if days != 1 else ''} ago"
    hours = total_seconds // 3600
    if hours > 0:
        return f"Added {hours} hour{'s' if hours != 1 else ''} ago"
    minutes = total_seconds // 60
    if minutes > 0:
        return f"Added {minutes} min ago"
    return "Added just now"
