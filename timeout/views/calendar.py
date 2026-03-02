import calendar as cal
from datetime import timedelta, date, datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from timeout.models import Event
from django.core.exceptions import ValidationError
from datetime import timedelta


@login_required
def calendar_view(request):
    """Renders a monthly calendar grid with events in day cells, including recurring events."""
    today = timezone.now().date()

    # Get today's date from the URL query string if nothing is provided
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    # Handle month overflow/underflow
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Build weeks grid starting from Monday
    cal_obj = cal.Calendar(firstweekday=0)
    weeks_raw = cal_obj.monthdatescalendar(year, month)

    # Determine visible range
    first_visible = weeks_raw[0][0]
    last_visible = weeks_raw[-1][-1]

    # Fetch events for visible date range
    lookahead_days = 365  # how far in the future you want to show recurring events
    events_qs = Event.objects.filter(
        creator=request.user,
        start_datetime__date__lte=last_visible + timedelta(days=lookahead_days),
    ).order_by("start_datetime")

    # Index events by date, including recurrence expansion
    events_by_date = {}
    for ev in events_qs:
        # Always add original event
        events_by_date.setdefault(ev.start_datetime.date(), []).append(ev)

        if ev.recurrence == 'none':
            continue  # skip non-recurring

        # Expand recurring events into visible range
        current_date = ev.start_datetime.date()
        while True:
            if ev.recurrence == 'daily':
                current_date += timedelta(days=1)
            elif ev.recurrence == 'weekly':
                current_date += timedelta(weeks=1)
            elif ev.recurrence == 'monthly':
                # Advance one month
                month_num = current_date.month + 1
                year_num = current_date.year
                if month_num > 12:
                    month_num = 1
                    year_num += 1
                day_num = min(current_date.day, cal.monthrange(year_num, month_num)[1])
                current_date = date(year_num, month_num, day_num)
            else:
                break

            if current_date > last_visible:
                break

            # Create a pseudo-event instance for display
            pseudo_event = {
                'original': ev,
                'recurrence_instance': True,
                'id': ev.id,  # pass the real ID
                'title': ev.title,
                'start_datetime': datetime.combine(current_date, ev.start_datetime.time()),
                'end_datetime': datetime.combine(current_date, ev.end_datetime.time()),
                'event_type': ev.event_type,
                'location': ev.location,
                'description': ev.description,
                'is_all_day': ev.is_all_day,
                'instance_date': current_date,  # the date this occurrence is shown
            }

            events_by_date.setdefault(current_date, []).append(pseudo_event)

    # Build weeks structure for template
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
    is_all_day = request.POST.get("is_all_day") == "on"
    allow_conflict = request.POST.get("allow_conflict") == "on"

    start_datetime = request.POST.get("start_datetime")
    end_datetime = request.POST.get("end_datetime")
    recurrence = request.POST.get("recurrence", "none")  # default 'none'

    if is_all_day:
        if not start_datetime:
            messages.error(request, "Please select a date for an all-day event.")
            return redirect("calendar")
        date_part = start_datetime.split("T")[0]
        start_datetime = f"{date_part}T00:00"
        end_datetime = f"{date_part}T23:59"
    else:
        if not start_datetime or not end_datetime:
            messages.error(request, "Start and end times are required.")
            return redirect("calendar")

    event = Event(
        creator=request.user,
        title=request.POST["title"],
        event_type=request.POST.get("event_type", "other"),
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        location=request.POST.get("location", ""),
        description=request.POST.get("description", ""),
        allow_conflict=allow_conflict,
        visibility=request.POST.get("visibility", "public"),
        is_all_day=is_all_day,
        recurrence=recurrence,
    )

    try:
        event.full_clean()
        event.save()
        messages.success(request, f'"{event.title}" added to calendar.')
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("calendar")