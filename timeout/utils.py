from datetime import datetime, date
from django.utils import timezone


def parse_aware_dt(dt_str):
    """Convert an ISO-format string to a timezone-aware datetime."""
    return timezone.make_aware(datetime.fromisoformat(dt_str))


def ai_cache_key(kind, user_id):
    """Build a daily per-user cache key for AI features."""
    return f"ai_{kind}_{user_id}_{date.today()}"
