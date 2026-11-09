"""
Tests for the public demo deployment: first-deploy seeding, the media route, the shared demo
account's locked actions, AI features without an API key, and the security fixes for the
password reset flow and the login redirect.
"""
import time
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
from django.views.static import serve

from timeout.models import Event
from timeout.utils import AI_DISABLED_MESSAGE

User = get_user_model()
TEST_PASSWORD = 'TestPass1!'


class BootstrapDemoCommandTests(TestCase):
    """The bootstrap command must seed an empty database and leave any other database alone."""

    @patch('timeout.management.commands.bootstrap_demo.call_command')
    def test_seeds_when_database_is_empty(self, mock_call_command):
        """An empty database gets seeded exactly once."""
        call_command('bootstrap_demo', stdout=StringIO())
        mock_call_command.assert_called_once()
        self.assertEqual(mock_call_command.call_args[0][0], 'seed')

    @patch('timeout.management.commands.bootstrap_demo.call_command')
    def test_skips_when_users_exist(self, mock_call_command):
        """A database with users is never re-seeded, since seed is not idempotent."""
        User.objects.create_user(username='existing', password=TEST_PASSWORD)
        output = StringIO()
        call_command('bootstrap_demo', stdout=output)
        mock_call_command.assert_not_called()
        self.assertIn('skipping', output.getvalue())


class MediaRouteTests(TestCase):
    """Uploaded media must be routed by Django whatever the DEBUG setting is."""

    def test_media_url_resolves_to_static_serve(self):
        """The /media/ route resolves to Django's file-serving view."""
        self.assertEqual(resolve('/media/profile_pictures/avatar.png').func, serve)


class DemoAccountLockTests(TestCase):
    """Visitors sharing the demo login must not be able to lock each other out."""

    def setUp(self):
        """Log in as the demo user."""
        self.demo_user = User.objects.create_user(username='demo', email='demo@timeout.example', password=TEST_PASSWORD)
        self.client.force_login(self.demo_user)

    def test_password_change_is_blocked(self):
        """The settings page refuses to change the demo password."""
        self.client.post(reverse('settings'), {
            'action': 'password', 'old_password': TEST_PASSWORD,
            'new_password1': 'Different9!Value', 'new_password2': 'Different9!Value',
        })
        self.demo_user.refresh_from_db()
        self.assertTrue(self.demo_user.check_password(TEST_PASSWORD))

    def test_account_deletion_is_blocked(self):
        """The settings page refuses to delete the demo account."""
        self.client.post(reverse('settings'), {'action': 'delete_account'})
        self.assertTrue(User.objects.filter(username='demo').exists())

    def test_username_change_is_blocked(self):
        """The demo username cannot be changed."""
        self.client.post(reverse('change_username'), {'new_username': 'renamed'})
        self.demo_user.refresh_from_db()
        self.assertEqual(self.demo_user.username, 'demo')

    def test_allauth_password_change_is_blocked(self):
        """allauth's own password change route cannot change the demo password either."""
        self.client.post('/accounts/password/change/', {
            'oldpassword': TEST_PASSWORD, 'password1': 'Different9!Value', 'password2': 'Different9!Value',
        })
        self.demo_user.refresh_from_db()
        self.assertTrue(self.demo_user.check_password(TEST_PASSWORD))

    def test_other_users_can_still_change_password(self):
        """The lock applies only to the demo account."""
        other_user = User.objects.create_user(username='student', password=TEST_PASSWORD)
        self.client.force_login(other_user)
        self.client.post(reverse('settings'), {
            'action': 'password', 'old_password': TEST_PASSWORD,
            'new_password1': 'Different9!Value', 'new_password2': 'Different9!Value',
        })
        other_user.refresh_from_db()
        self.assertTrue(other_user.check_password('Different9!Value'))


@override_settings(OPENAI_API_KEY='')
class AiDisabledTests(TestCase):
    """With no API key, every AI feature must explain itself instead of failing."""

    def setUp(self):
        """Create a user with a deadline and an upcoming study session."""
        self.user = User.objects.create_user(username='student', password=TEST_PASSWORD)
        self.client.force_login(self.user)
        start_time = timezone.now() + timedelta(days=5)
        self.deadline = Event.objects.create(
            creator=self.user, title='Coursework', event_type=Event.EventType.DEADLINE,
            start_datetime=start_time, end_datetime=start_time + timedelta(minutes=1),
        )
        self.study_session = Event.objects.create(
            creator=self.user, title='Revision', event_type=Event.EventType.STUDY_SESSION,
            start_datetime=start_time - timedelta(days=1),
            end_datetime=start_time - timedelta(days=1) + timedelta(hours=1),
        )

    def _assert_disabled_response(self, response):
        """Check a JSON endpoint returned the disabled message without an error status."""
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertTrue(response_data['ai_disabled'])
        self.assertEqual(response_data['error'], AI_DISABLED_MESSAGE)

    def test_add_event_returns_message(self):
        """AI add event explains that AI is disabled."""
        self._assert_disabled_response(
            self.client.post(reverse('ai_event_create'), {'user_input': 'meeting tomorrow'}))

    def test_reschedule_all_returns_message(self):
        """Rescheduling all sessions explains that AI is disabled, with no call to OpenAI."""
        with patch('timeout.services.openai_service.call_openai') as mock_call_openai:
            self._assert_disabled_response(self.client.post(reverse('reschedule_study_sessions')))
        mock_call_openai.assert_not_called()

    def test_suggest_single_session_returns_message(self):
        """Suggesting a slot for one session explains that AI is disabled."""
        self._assert_disabled_response(
            self.client.post(reverse('ai_reschedule'), {'event_id': self.study_session.pk}))

    def test_plan_study_still_works_without_ai(self):
        """Plan Study falls back to the built-in scheduler."""
        response = self.client.post(reverse('study_planner_plan'), {
            'event_id': self.deadline.pk, 'hours_needed': 4, 'session_length': 2,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(response.json()['sessions'])

    def test_dashboard_shows_message(self):
        """The dashboard shows the message where the weekly briefing would appear."""
        self.assertContains(self.client.get(reverse('dashboard')), AI_DISABLED_MESSAGE)

    def test_calendar_shows_message_and_disables_buttons(self):
        """The calendar's AI modals show the message and disable their AI actions."""
        response = self.client.get(reverse('calendar'))
        self.assertContains(response, AI_DISABLED_MESSAGE)
        self.assertContains(response, 'onclick="submitAiEvent()" disabled')
        self.assertContains(response, 'onclick="fetchRescheduleSuggestions()" disabled')
        self.assertContains(response, 'Plan Sessions')

    @override_settings(OPENAI_API_KEY='test-key')
    def test_calendar_hides_message_when_key_is_set(self):
        """With a key configured, the calendar shows no disabled message."""
        with patch('timeout.services.ai_service.AIService.get_workload_warning', return_value=None), \
                patch('timeout.services.ai_service.AIService.get_suggestions', return_value=[]):
            response = self.client.get(reverse('calendar'))
        self.assertNotContains(response, AI_DISABLED_MESSAGE)
        self.assertContains(response, 'Plan with AI')


class PasswordResetSecurityTests(TestCase):
    """The reset code must not be guessable or usable once sending fails."""

    def setUp(self):
        """Create a user and store the forgot password URL."""
        self.user = User.objects.create_user(username='student', email='student@example.com', password=TEST_PASSWORD)
        self.url = reverse('forgot_password')

    def _start_reset(self, code='123456'):
        """Put a valid reset code in the test client's session."""
        session = self.client.session
        session.update({'reset_code': code, 'reset_user_id': self.user.pk, 'reset_code_time': time.time()})
        session.save()

    @patch('timeout.views.password_reset.EmailService.send_reset_code', return_value=False)
    def test_failed_send_leaves_no_code_in_session(self, mock_send):
        """A code that was never delivered must not stay in the session to be guessed."""
        self.client.post(self.url, {'step': 'request', 'identifier': 'student@example.com'})
        self.assertNotIn('reset_code', self.client.session)
        self.assertNotIn('reset_user_id', self.client.session)

    def test_correct_code_is_accepted(self):
        """The right code still reaches the reset page."""
        self._start_reset()
        response = self.client.post(self.url, {'step': 'verify', 'code': '123456'})
        self.assertRedirects(response, reverse('reset_password'))

    def test_too_many_wrong_codes_discards_code(self):
        """Five wrong guesses discard the code, so even the right code then fails."""
        self._start_reset()
        for _ in range(5):
            response = self.client.post(self.url, {'step': 'verify', 'code': '000000'})
        self.assertEqual(response.context['step'], 'request')
        self.assertNotIn('reset_code', self.client.session)
        response = self.client.post(self.url, {'step': 'verify', 'code': '123456'})
        self.assertNotIn('reset_verified', self.client.session)

    def test_wrong_code_under_limit_allows_retry(self):
        """A single wrong guess keeps the code active."""
        self._start_reset()
        response = self.client.post(self.url, {'step': 'verify', 'code': '000000'})
        self.assertEqual(response.context['step'], 'verify')
        self.assertIn('reset_code', self.client.session)


class LoginRedirectSecurityTests(TestCase):
    """The login page must only redirect to pages on this site."""

    def setUp(self):
        """Create a user and the login form data."""
        User.objects.create_user(username='student', email='student@example.com', password=TEST_PASSWORD)
        self.credentials = {'username': 'student', 'password': TEST_PASSWORD}

    def test_external_next_goes_to_dashboard(self):
        """An external next URL is ignored."""
        response = self.client.post(reverse('login') + '?next=https://evil.example/', self.credentials)
        self.assertRedirects(response, reverse('dashboard'))

    def test_scheme_relative_next_goes_to_dashboard(self):
        """A scheme-relative next URL is ignored."""
        response = self.client.post(reverse('login') + '?next=//evil.example/', self.credentials)
        self.assertRedirects(response, reverse('dashboard'))

    def test_internal_next_is_followed(self):
        """A next URL on this site is still followed."""
        response = self.client.post(reverse('login') + '?next=/profile/', self.credentials)
        self.assertRedirects(response, '/profile/')
