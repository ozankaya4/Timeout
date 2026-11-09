"""
bootstrap_demo.py - Seeds demo data on first deploy only.

The seed command is not idempotent, so this runs it only when the database has no
users. Using one transaction means a failed seed leaves the database empty and the
next container start tries again, rather than skipping a half-seeded database.
"""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """Management command to seed demo data when the database is empty."""
    help = 'Run the seed command once, only if the database has no users.'

    def handle(self, *args, **options):
        """Seed inside one transaction, or skip if any user already exists."""
        if get_user_model().objects.exists():
            self.stdout.write('Database already has users, skipping demo seed.')
            return
        with transaction.atomic():
            call_command('seed', stdout=self.stdout)
