"""
reseed_demo.py - Safely replaces the demo data on a deployed site.

The unseed command deletes every user, including people who signed up, and the seed
command touches every user in the database. So this command refuses to run while
accounts exist that seeding didn't create, unless told to delete them. It takes a
database backup first and runs both commands in one transaction, so a failure leaves
the existing data in place.
"""

import os
import sqlite3
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

User = get_user_model()

SUPERUSER_USERNAME = 'johndoe'

# Seeding runs in one short transaction, so later accounts came from real signups.
SEED_WINDOW = timedelta(minutes=10)


def find_signups():
    """Return users that were not created by the seeding run."""
    seeded_superuser = User.objects.filter(username=SUPERUSER_USERNAME).first()
    if seeded_superuser is None:
        return User.objects.all()
    return User.objects.filter(date_joined__gt=seeded_superuser.date_joined + SEED_WINDOW)


def backup_database(backup_directory):
    """Copy the live SQLite database, including any WAL data, and return the backup path."""
    timestamp = timezone.now().strftime('%Y%m%dT%H%M%SZ')
    backup_path = Path(backup_directory) / f'db-before-reseed-{timestamp}.sqlite3'
    connection.ensure_connection()
    backup_connection = sqlite3.connect(backup_path)
    try:
        connection.connection.backup(backup_connection)
    finally:
        backup_connection.close()
    return backup_path


class Command(BaseCommand):
    """Management command to back up the database and replace its demo data."""
    help = 'Back up the database, then replace all demo data in one transaction.'

    def add_arguments(self, parser):
        """Add options for previewing the run, signups, and the backup location."""
        parser.add_argument('--dry-run', action='store_true', help='Report what would happen and change nothing.')
        parser.add_argument('--delete-signups', action='store_true', help='Also delete accounts seeding did not create.')
        parser.add_argument('--backup-directory', help='Backup location. Defaults to the database directory.')

    def handle(self, *args, **options):
        """Check it is safe to proceed, back up, then unseed and seed atomically."""
        self._require_private_admin_password()
        signups = find_signups()
        self.stdout.write(f'Users: {User.objects.count()}. Accounts seeding did not create: {signups.count()}.')
        if options['dry_run']:
            self._report_signups(signups)
            self.stdout.write('Dry run: nothing changed.')
            return
        if signups.exists() and not options['delete_signups']:
            self._report_signups(signups)
            raise CommandError('Refusing to delete these accounts. Re-run with --delete-signups to remove them.')
        backup_directory = options['backup_directory'] or Path(connection.settings_dict['NAME']).parent
        self.stdout.write(f'Backup: {backup_database(backup_directory)}')
        with transaction.atomic():
            call_command('unseed', stdout=self.stdout)
            call_command('seed', stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS('Demo data replaced.'))

    def _require_private_admin_password(self):
        """Stop a deployed site from getting the published default admin password."""
        if not settings.DEBUG and not os.environ.get('SEED_SUPERUSER_PASSWORD'):
            raise CommandError('Set SEED_SUPERUSER_PASSWORD before re-seeding a deployed site.')

    def _report_signups(self, signups):
        """List the accounts that re-seeding would delete."""
        for signup in signups:
            self.stdout.write(f'  @{signup.username} joined {signup.date_joined:%Y-%m-%d %H:%M}')
