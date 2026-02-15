from unittest.mock import MagicMock, patch

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

from timeout.adapters import TimeoutSocialAccountAdapter

User = get_user_model()


class TimeoutSocialAccountAdapterTests(TestCase):
    """Tests for the custom SocialAccountAdapter."""

    def setUp(self):
        self.adapter = TimeoutSocialAccountAdapter()
        self.factory = RequestFactory()

    # ── _profile_incomplete ───────────────────────────────

    def test_profile_incomplete_missing_university(self):
        user = User(username='testuser', year_of_study=2, university='')
        self.assertTrue(self.adapter._profile_incomplete(user))

    def test_profile_incomplete_missing_year(self):
        user = User(username='testuser', university='Oxford', year_of_study=None)
        self.assertTrue(self.adapter._profile_incomplete(user))

    def test_profile_incomplete_auto_generated_username(self):
        user = User(username='user_12345', university='Oxford', year_of_study=2)
        self.assertTrue(self.adapter._profile_incomplete(user))

    def test_profile_complete(self):
        user = User(username='realuser', university='Oxford', year_of_study=2)
        self.assertFalse(self.adapter._profile_incomplete(user))

    # ── get_login_redirect_url ────────────────────────────

    def test_redirect_to_complete_profile_if_incomplete(self):
        request = self.factory.get('/')
        request.user = User(username='user_abc', university='', year_of_study=None)
        url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(url, '/complete-profile/')

    def test_redirect_to_dashboard_if_complete(self):
        request = self.factory.get('/')
        request.user = User(username='realuser', university='Oxford', year_of_study=3)
        url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(url, '/dashboard/')

    # ── pre_social_login ──────────────────────────────────

    def test_pre_social_login_links_existing_user_by_email(self):
        user = User.objects.create_user(
            username='existing', email='match@example.com', password='Pass1234!'
        )

        request = self.factory.get('/')
        request.session = SessionStore()

        sociallogin = MagicMock()
        sociallogin.account.extra_data = {'email': 'match@example.com'}
        sociallogin.is_existing = False

        self.adapter.pre_social_login(request, sociallogin)
        sociallogin.connect.assert_called_once_with(request, user)

    def test_pre_social_login_skips_if_already_connected(self):
        User.objects.create_user(
            username='existing2', email='connected@example.com', password='Pass1234!'
        )

        request = self.factory.get('/')
        sociallogin = MagicMock()
        sociallogin.account.extra_data = {'email': 'connected@example.com'}
        sociallogin.is_existing = True

        self.adapter.pre_social_login(request, sociallogin)
        sociallogin.connect.assert_not_called()

    def test_pre_social_login_skips_if_no_email(self):
        request = self.factory.get('/')
        sociallogin = MagicMock()
        sociallogin.account.extra_data = {}
        sociallogin.email_addresses = []

        self.adapter.pre_social_login(request, sociallogin)
        sociallogin.connect.assert_not_called()

    def test_pre_social_login_skips_if_no_matching_user(self):
        request = self.factory.get('/')
        sociallogin = MagicMock()
        sociallogin.account.extra_data = {'email': 'nobody@example.com'}
        sociallogin.is_existing = False

        self.adapter.pre_social_login(request, sociallogin)
        sociallogin.connect.assert_not_called()

    def test_pre_social_login_uses_email_addresses_fallback(self):
        user = User.objects.create_user(
            username='fallback', email='fallback@example.com', password='Pass1234!'
        )

        request = self.factory.get('/')
        request.session = SessionStore()

        email_obj = MagicMock()
        email_obj.email = 'fallback@example.com'

        sociallogin = MagicMock()
        sociallogin.account.extra_data = {}
        sociallogin.email_addresses = [email_obj]
        sociallogin.is_existing = False

        self.adapter.pre_social_login(request, sociallogin)
        sociallogin.connect.assert_called_once_with(request, user)
