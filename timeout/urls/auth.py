from django.urls import path
from timeout.views import auth

urlpatterns = [
    path('signup/', auth.signup_view, name='signup'),
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),
    path('complete-profile/', auth.complete_profile, name='complete_profile'),
]
