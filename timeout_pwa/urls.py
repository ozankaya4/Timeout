"""
URL configuration for timeout_pwa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.views.static import serve

from allauth.socialaccount.views import SignupView
from timeout.sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    # Override allauth's socialaccount signup to use our custom template
    path(
        'accounts/social/signup/',
        SignupView.as_view(template_name='auth/google_signin.html'),
        name='socialaccount_signup',
    ),
    path('accounts/', include('allauth.urls')),
    path('', include('timeout.urls')),
    # Uploaded profile pictures. Django serves these directly so the reverse proxy
    # does not need access to the app's data volume; traffic here is demo-sized.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
