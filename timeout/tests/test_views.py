from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class PublicPageTests(TestCase):
    """Tests for pages accessible without authentication."""

    def test_landing_page(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'timeout/landing.html')

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'timeout/login.html')

    def test_signup_page(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'timeout/signup.html')


class AuthenticatedPageTests(TestCase):
    """Tests for pages accessible after login."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='pageuser', password='TestPass1!'
        )
        self.client.login(username='pageuser', password='TestPass1!')

    def test_dashboard(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_calendar(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)

    def test_notes(self):
        response = self.client.get(reverse('notes'))
        self.assertEqual(response.status_code, 200)

    def test_statistics(self):
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)

    def test_social(self):
        response = self.client.get(reverse('social'))
        self.assertEqual(response.status_code, 200)


class SignupViewTests(TestCase):
    """Tests for the signup view logic."""

    def test_signup_get_returns_form(self):
        response = self.client.get(reverse('signup'))
        self.assertIn('form', response.context)

    def test_signup_post_valid(self):
        response = self.client.post(reverse('signup'), {
            'username': 'brand_new',
            'email': 'brand@example.com',
            'first_name': 'Brand',
            'last_name': 'New',
            'password1': 'Str0ng@Pass!',
            'password2': 'Str0ng@Pass!',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='brand_new').exists())

    def test_signup_post_logs_user_in(self):
        self.client.post(reverse('signup'), {
            'username': 'autouser',
            'email': 'auto@example.com',
            'first_name': 'Auto',
            'last_name': 'User',
            'password1': 'Str0ng@Pass!',
            'password2': 'Str0ng@Pass!',
        })
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         User.objects.get(username='autouser').pk)

    def test_signup_post_invalid_rerenders(self):
        response = self.client.post(reverse('signup'), {
            'username': 'bad',
            'email': 'bad@example.com',
            'password1': 'short',
            'password2': 'short',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'timeout/signup.html')
        self.assertFalse(User.objects.filter(username='bad').exists())

    def test_signup_redirects_authenticated_user(self):
        User.objects.create_user(username='already', password='TestPass1!')
        self.client.login(username='already', password='TestPass1!')
        response = self.client.get(reverse('signup'))
        self.assertRedirects(response, reverse('dashboard'))


class LoginViewTests(TestCase):
    """Tests for the login view logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='TestPass1!'
        )

    def test_login_get_returns_form(self):
        response = self.client.get(reverse('login'))
        self.assertIn('form', response.context)

    def test_login_post_valid(self):
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'TestPass1!',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_post_valid_with_next(self):
        url = reverse('login') + '?next=/profile/'
        response = self.client.post(url, {
            'username': 'loginuser',
            'password': 'TestPass1!',
        })
        self.assertRedirects(response, '/profile/')

    def test_login_post_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'timeout/login.html')

    def test_login_redirects_authenticated_user(self):
        self.client.login(username='loginuser', password='TestPass1!')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard'))


class LogoutViewTests(TestCase):
    """Tests for the logout view logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='logoutuser', password='TestPass1!'
        )
        self.client.login(username='logoutuser', password='TestPass1!')

    def test_logout_redirects_to_landing(self):
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('landing'))

    def test_logout_ends_session(self):
        self.client.get(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
