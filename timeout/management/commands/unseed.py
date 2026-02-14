"""
Custom management command to clear seeded users from the database.

Usage:
    python manage.py unseed          # Keep superuser @johndoe
    python manage.py unseed --all    # Remove everyone including superusers
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SUPERUSER_USERNAME = 'johndoe'


class Command(BaseCommand):
    help = 'Remove all seeded users from the database (preserves @johndoe by default).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            dest='remove_all',
            help='Remove ALL users including the superuser @johndoe.',
        )

    def handle(self, *args, **options):
        remove_all = options['remove_all']
        total_before = User.objects.count()

        if total_before == 0:
            self.stdout.write(self.style.WARNING('Database is already empty.'))
            return

        if remove_all:
            self.stdout.write(self.style.WARNING(
                'Mode: Removing ALL users (including superusers)'
            ))
            User.objects.all().delete()
        else:
            self.stdout.write('Mode: Removing seeded users (keeping @johndoe)')
            User.objects.exclude(username=SUPERUSER_USERNAME).delete()

        total_after = User.objects.count()
        removed = total_before - total_after

        self.stdout.write(self.style.SUCCESS(f'Removed {removed} user(s).'))
        self.stdout.write(f'Remaining users: {total_after}')
