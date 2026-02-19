from django.shortcuts import get_object_or_404, redirect, render
from timeout.models import Event

def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        event.title = request.POST.get("title")
        event.start_datetime = request.POST.get("start_datetime")
        event.end_datetime = request.POST.get("end_datetime")
        event.description = request.POST.get("description")
        event.location = request.POST.get("location")
        event.event_type = request.POST.get("event_type")
        event.allow_conflict = request.POST.get("allow_conflict") == "on"
        event.save()
        return redirect("event_details", event_id=event.pk)  # ← fixed

    return render(request, "pages/event_form.html", {"event": event})
