from django.shortcuts import render


def landing(request):
    """Landing page view."""
    return render(request, 'timeout/landing.html')


def login_view(request):
    """Login page view."""
    return render(request, 'timeout/login.html')


def signup(request):
    """Signup page view."""
    return render(request, 'timeout/signup.html')


def dashboard(request):
    """Dashboard page view."""
    return render(request, 'timeout/dashboard.html')


def profile(request):
    """Profile page view."""
    return render(request, 'timeout/profile.html')


def calendar(request):
    """Calendar page view."""
    return render(request, 'timeout/calendar.html')


def notes(request):
    """Notes page view."""
    return render(request, 'timeout/notes.html')


def statistics(request):
    """Statistics page view."""
    return render(request, 'timeout/statistics.html')


def social(request):
    """Social page view."""
    return render(request, 'timeout/social.html')
