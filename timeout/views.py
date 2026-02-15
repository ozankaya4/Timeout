from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import SignupForm, LoginForm, CompleteProfileForm


def landing(request):
    """Landing page view."""
    return render(request, 'timeout/landing.html')


def signup_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = SignupForm()

    return render(request, 'timeout/signup.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'timeout/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


@login_required
def complete_profile(request):
    """Let social-auth users fill in missing profile fields."""
    if request.method == 'POST':
        form = CompleteProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile completed successfully!')
            return redirect('dashboard')
    else:
        form = CompleteProfileForm(instance=request.user)

    return render(request, 'timeout/complete_profile.html', {'form': form})


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
