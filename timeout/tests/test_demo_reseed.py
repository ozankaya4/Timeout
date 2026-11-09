"""
Tests for demo seed dates and the reseed_demo command. Seeded dates must be relative to the
seeding date, mostly upcoming, with very few overdue items. Re-seeding must not delete real
signups by accident, and must leave existing data in place if it fails.
"""
import os
import sqlite3
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from timeout.models import Event, Note
from timeout.services import DeadlineService

User = get_user_model()
RESEED_MODULE = 'timeout.management.commands.reseed_demo'
ADMIN_PASSWORD_ENV = {'SEED_SUPERUSER_PASSWORD': 'private-test-value'}


class SeedDateTests(TestCase):
    """Checks on the dates and completion state that seeding produces."""

    @classmethod
    def setUpTestData(cls):
        """Seed once, since every test only reads the result."""
        cls.now = timezone.now()
        call_command('seed', stdout=StringIO())
        cls.demo_user = User.objects.get(username='demo')
        cls.johndoe = User.objects.get(username='johndoe')

    def _overdue_count(self, user):
        """Count the items the dashboard and deadlines page would label overdue."""
        active_events = DeadlineService.get_active_deadlines(user)
        return sum(item['urgency_status'] == 'overdue' for item in active_events)

    def test_showcase_accounts_have_at_most_two_overdue_items(self):
        """Each account shows its overdue deadline, plus at most a class ending during the test run."""
        for user in (self.demo_user, self.johndoe):
            self.assertGreaterEqual(self._overdue_count(user), 1)
            self.assertLessEqual(self._overdue_count(user), 2)

    def test_only_deliberate_deadlines_are_overdue_across_all_users(self):
        """Every other past event is marked complete, so nobody else shows overdue items."""
        incomplete_past_events = Event.objects.filter(
            creator__isnull=False, end_datetime__lte=self.now, is_completed=False,
        )
        self.assertEqual(incomplete_past_events.count(), 2)
        self.assertEqual(set(incomplete_past_events.values_list('event_type', flat=True)), {'deadline'})

    def test_schedule_is_mostly_upcoming(self):
        """Upcoming events far outnumber past ones on the showcase account."""
        events = self.johndoe.created_events.all()
        upcoming_count = events.filter(start_datetime__gt=self.now).count()
        self.assertGreater(upcoming_count, events.count() * 0.8)

    def test_a_few_recently_completed_events(self):
        """Completed events are few, and all from the past week."""
        completed_events = self.johndoe.created_events.filter(is_completed=True)
        self.assertGreaterEqual(completed_events.count(), 6)
        self.assertLessEqual(completed_events.count(), 7)
        self.assertFalse(completed_events.filter(start_datetime__lt=self.now - timedelta(days=8)).exists())

    def test_dates_are_relative_to_seeding_date(self):
        """No event starts more than two weeks before seeding, apart from fixed global holidays."""
        oldest_allowed = self.now - timedelta(days=15)
        self.assertFalse(Event.objects.filter(creator__isnull=False, start_datetime__lt=oldest_allowed).exists())

    def test_no_notes_are_overdue(self):
        """Seeded note due dates are all in the future."""
        self.assertFalse(Note.objects.filter(due_date__lte=self.now).exists())


@patch.dict(os.environ, ADMIN_PASSWORD_ENV)
class ReseedDemoSafetyTests(TestCase):
    """Checks that re-seeding refuses unsafe runs and is all-or-nothing."""

    def setUp(self):
        """Create a seeded-looking admin and one student."""
        User.objects.create_superuser(username='johndoe', email='john@example.com', password='x')
        User.objects.create_user(username='student', password='x')

    def _add_signup(self):
        """Create an account that joined well after seeding."""
        signup = User.objects.create_user(username='real_person', password='x')
        User.objects.filter(pk=signup.pk).update(date_joined=timezone.now() + timedelta(days=1))

    def test_refuses_when_signups_exist(self):
        """Real signups stop the run, before any backup or deletion."""
        self._add_signup()
        with patch(f'{RESEED_MODULE}.backup_database') as mock_backup, \
                patch(f'{RESEED_MODULE}.call_command') as mock_call_command:
            with self.assertRaises(CommandError):
                call_command('reseed_demo', stdout=StringIO())
        mock_backup.assert_not_called()
        mock_call_command.assert_not_called()
        self.assertTrue(User.objects.filter(username='real_person').exists())

    def test_delete_signups_flag_allows_the_run(self):
        """The explicit flag lets the run continue."""
        self._add_signup()
        with patch(f'{RESEED_MODULE}.backup_database'), patch(f'{RESEED_MODULE}.call_command') as mock_call_command:
            call_command('reseed_demo', '--delete-signups', stdout=StringIO())
        self.assertEqual([call.args[0] for call in mock_call_command.call_args_list], ['unseed', 'seed'])

    def test_dry_run_changes_nothing(self):
        """A dry run reports signups without backing up or seeding."""
        self._add_signup()
        output = StringIO()
        with patch(f'{RESEED_MODULE}.backup_database') as mock_backup, \
                patch(f'{RESEED_MODULE}.call_command') as mock_call_command:
            call_command('reseed_demo', '--dry-run', stdout=output)
        mock_backup.assert_not_called()
        mock_call_command.assert_not_called()
        self.assertIn('real_person', output.getvalue())

    def test_failed_seed_restores_existing_data(self):
        """If seeding fails after unseed has deleted everything, the deletion is rolled back."""
        def unseed_then_fail(command_name, **kwargs):
            if command_name == 'seed':
                raise RuntimeError('seed failed')
            real_call_command(command_name, stdout=StringIO())

        real_call_command = call_command
        with patch(f'{RESEED_MODULE}.backup_database'), \
                patch(f'{RESEED_MODULE}.call_command', side_effect=unseed_then_fail):
            with self.assertRaises(RuntimeError):
                call_command('reseed_demo', stdout=StringIO())
        self.assertTrue(User.objects.filter(username='student').exists())

    def test_requires_private_admin_password_on_deployed_site(self):
        """Without the env var, a deployed site must not get the published default password."""
        without_password = {key: value for key, value in os.environ.items() if key != 'SEED_SUPERUSER_PASSWORD'}
        with patch.dict(os.environ, without_password, clear=True), self.settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command('reseed_demo', stdout=StringIO())


@patch.dict(os.environ, ADMIN_PASSWORD_ENV)
class ReseedDemoBackupTests(TransactionTestCase):
    """A real SQLite backup needs no open transaction, so this can't use TestCase."""

    def test_backup_contains_current_data(self):
        """The backup is a readable database holding the data from before the re-seed."""
        User.objects.create_superuser(username='johndoe', email='john@example.com', password='x')
        with tempfile.TemporaryDirectory() as backup_directory, \
                patch(f'{RESEED_MODULE}.call_command'):
            call_command('reseed_demo', f'--backup-directory={backup_directory}', stdout=StringIO())
            backup_files = list(Path(backup_directory).glob('db-before-reseed-*.sqlite3'))
            self.assertEqual(len(backup_files), 1)
            backup_connection = sqlite3.connect(backup_files[0])
            try:
                usernames = backup_connection.execute('SELECT username FROM timeout_user').fetchall()
            finally:
                backup_connection.close()
        self.assertEqual(usernames, [('johndoe',)])
