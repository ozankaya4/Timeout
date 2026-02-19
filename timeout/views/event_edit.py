from django.shortcuts import get_object_or_404, redirect, render
from timeout.models import Event

def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        event.title = request.POST.get("title")
        event.date = request.POST.get("date")
        event.start_time = request.POST.get("start_time")
        event.end_time = request.POST.get("end_time")
        event.description = request.POST.get("description")
        event.allow_conflict = request.POST.get("allow_conflict") == "on"
        event.save()
        return redirect("event_details", pk=event.pk)

    return render(request, "timeout/event_form.html", {"event": event})
