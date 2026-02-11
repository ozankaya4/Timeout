from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('calendar/', views.calendar, name='calendar'),
    path('notes/', views.notes, name='notes'),
    path('statistics/', views.statistics, name='statistics'),
    path('social/', views.social, name='social'),
]
