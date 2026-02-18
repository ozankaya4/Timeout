import calendar as cal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from timeout.models import Event


@login_required
def calendar_view(request):
    """Renders a monthly calendar grid with events in day cells."""
    """
    Calendar template that allows to add events calculates time left
    """
    today = timezone.now().date()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    # Get months
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Build weeks grid (Monday start)
    cal_obj = cal.Calendar(firstweekday=0)
    weeks_raw = cal_obj.monthdatescalendar(year, month)

    # Query events for visible date range
    first_visible = weeks_raw[0][0]
    last_visible = weeks_raw[-1][-1]
    events_qs = Event.objects.filter(
        creator=request.user,
        start_datetime__date__gte=first_visible,
        start_datetime__date__lte=last_visible,
    ).order_by("start_datetime")

    # Index by date for O(1) lookup in template
    events_by_date = {}
    for ev in events_qs:
        events_by_date.setdefault(ev.start_datetime.date(), []).append(ev)

    # Structure for template
    weeks = []
    for week in weeks_raw:
        days = []
        for day in week:
            days.append({
                "date": day,
                "day_num": day.day,
                "in_month": day.month == month,
                "is_today": day == today,
                "events": events_by_date.get(day, []),
            })
        weeks.append(days)

    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    context = {
        "weeks": weeks,
        "year": year,
        "month": month,
        "month_name": month_names[month],
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    }
    return render(request, "pages/calendar.html", context)


@login_required
@require_POST
def event_create(request):
    """Handle the Add Event model form submission."""
    try:
        event = Event(
            creator=request.user,
            title=request.POST["title"],
            event_type=request.POST.get("event_type", "other"),
            start_datetime=request.POST["start_datetime"],
            end_datetime=request.POST["end_datetime"],
            location=request.POST.get("location", ""),
            description=request.POST.get("description", ""),
        )
        event.full_clean()
        event.save()
        messages.success(request, f'"{event.title}" added to calendar.')
    except Exception as e:
        messages.error(request, f"Could not create event: {e}")

    return redirect("calendar")