from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from timeout.models import Event
from django.core.exceptions import ValidationError

def event_edit(request, pk):
    """Edit an existing event."""
    event = get_object_or_404(Event, pk=pk, creator=request.user)

    if request.method == "POST":
        # Update event fields from form
        event.title = request.POST.get("title", event.title)
        event.start_datetime = request.POST.get("start_datetime", event.start_datetime)
        event.end_datetime = request.POST.get("end_datetime", event.end_datetime)
        event.description = request.POST.get("description", "")
        event.location = request.POST.get("location", "")
        event.event_type = request.POST.get("event_type", "other")
        event.visibility = request.POST.get("visibility", "public")
        event.allow_conflict = request.POST.get("allow_conflict") == "on"

        try:
            event.full_clean()  # Validate all fields
            event.save()
            messages.success(request, f'Event "{event.title}" updated successfully.')
            return redirect("calendar")  # ← go back to calendar
        except ValidationError as e:
            messages.error(request, "Error updating event: " + str(e))
        except Exception as e:
            messages.error(request, "Unexpected error: " + str(e))

    return render(request, "pages/event_form.html", {"event": event})