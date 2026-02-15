from django.urls import path, include

urlpatterns = [
    path('', include('timeout.urls.auth')),
    path('', include('timeout.urls.pages')),
]
