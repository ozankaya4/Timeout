from django.urls import path
from timeout.views import pages

urlpatterns = [
    path('', pages.landing, name='landing'),
    path('dashboard/', pages.dashboard, name='dashboard'),
    path('profile/', pages.profile, name='profile'),
    path('calendar/', pages.calendar, name='calendar'),
    path('notes/', pages.notes, name='notes'),
    path('statistics/', pages.statistics, name='statistics'),
    path('social/', pages.social, name='social'),
]
