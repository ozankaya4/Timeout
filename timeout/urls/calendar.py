"""
from django.urls import path
from . import views
#not needed?
urlpatterns = [

    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/add/', views.event_create, name='event_create'),

    
]
"""