from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def landing(request):
    """Landing page view."""
    return render(request, 'timeout/pages/landing.html')


@login_required
def dashboard(request):
    """Dashboard page view."""
    return render(request, 'timeout/pages/dashboard.html')


@login_required
def profile(request):
    """Profile page view."""
    return render(request, 'timeout/pages/profile.html')


@login_required
def calendar(request):
    """Calendar page view."""
    return render(request, 'timeout/pages/calendar.html')


@login_required
def notes(request):
    """Notes page view."""
    return render(request, 'timeout/pages/notes.html')


@login_required
def statistics(request):
    """Statistics page view."""
    return render(request, 'timeout/pages/statistics.html')


@login_required
def social(request):
    """Social page view."""
    return render(request, 'timeout/social/social.html')
