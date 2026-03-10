from django.urls import path
from timeout.views import calendar as cal_views
from timeout.views import deadlines as deadline_views
from timeout.views import ai_calendar as ai_cal_views

from timeout.views import event_edit as edit_views
from timeout.views import event_details as detail_views
from timeout.views import event_delete as delete_views

urlpatterns = [
    path('calendar/', cal_views.calendar_view, name='calendar'),
    path('calendar/add/', cal_views.event_create, name='event_create'),
    path('calendar/ai-add/', ai_cal_views.ai_create_event, name='ai_event_create'),
    path('deadlines/', deadline_views.deadline_list_view, name='deadline_list'),
    path('deadlines/<int:event_id>/complete/', deadline_views.deadline_mark_complete, name='deadline_mark_complete',),
    # Event CRUD – click an event to view/edit/delete
    path('event/<int:event_id>/', detail_views.event_details, name='event_details'),
    path('event/<int:pk>/edit/', edit_views.event_edit, name='event_edit'),
    path('event/<int:pk>/delete/', delete_views.event_delete, name='event_delete'),
]