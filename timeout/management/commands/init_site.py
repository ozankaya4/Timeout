"""
One-time management command to ensure a Site object with id=1 exists.

Usage:
    python manage.py init_site
    
This fixes the "Site matching query does not exist" error that occurs
when django.contrib.sites / allauth tries to look up SITE_ID = 1.
"""

import os

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


DOMAIN = os.environ.get('SITE_DOMAIN', '127.0.0.1:8000')
NAME = os.environ.get('SITE_NAME', 'Timeout Local')


class Command(BaseCommand):
    """Management command to create or update the Site record (id=1) used by allauth."""
    help = 'Create or update the Site record (id=1) used by allauth.'

    def handle(self, *args, **options):
        """ Remove every existing Site record so we start clean.
            This avoids unique-constraint clashes on domain. """
        Site.objects.all().delete()
        Site.objects.create(id=1, domain=DOMAIN, name=NAME)
        self.stdout.write(self.style.SUCCESS(
            f'Created Site(id=1, domain="{DOMAIN}", name="{NAME}")'))
