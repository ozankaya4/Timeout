from django.test import TestCase
from django.contrib.auth import get_user_model

from timeout.forms import SignupForm, LoginForm

User = get_user_model()


class SignupFormTests(TestCase):
    """Tests for the SignupForm validation logic."""

    def _form_data(self, **overrides):
        """Return valid signup data with optional overrides."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'Strong@Pass1',
            'password2': 'Strong@Pass1',
        }
        data.update(overrides)
        return data

    # ── Valid submission ──────────────────────────────────

    def test_valid_form(self):
        form = SignupForm(data=self._form_data())
        self.assertTrue(form.is_valid())

    def test_save_creates_user(self):
        form = SignupForm(data=self._form_data())
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('Strong@Pass1'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_save_without_commit(self):
        form = SignupForm(data=self._form_data())
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)
        self.assertIsNone(user.pk)

    # ── Password too short ────────────────────────────────

    def test_password_too_short(self):
        form = SignupForm(data=self._form_data(password1='Ab1!', password2='Ab1!'))
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)
        self.assertIn('at least 8 characters', form.errors['password1'][0])

    # ── Missing uppercase ─────────────────────────────────

    def test_password_no_uppercase(self):
        form = SignupForm(data=self._form_data(
            password1='strong@pass1', password2='strong@pass1'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('uppercase', form.errors['password1'][0])

    # ── Missing lowercase ─────────────────────────────────

    def test_password_no_lowercase(self):
        form = SignupForm(data=self._form_data(
            password1='STRONG@PASS1', password2='STRONG@PASS1'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('lowercase', form.errors['password1'][0])

    # ── Missing digit ─────────────────────────────────────

    def test_password_no_digit(self):
        form = SignupForm(data=self._form_data(
            password1='Strong@Pass', password2='Strong@Pass'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('number', form.errors['password1'][0])

    # ── Missing symbol ────────────────────────────────────

    def test_password_no_symbol(self):
        form = SignupForm(data=self._form_data(
            password1='StrongPass1', password2='StrongPass1'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('special character', form.errors['password1'][0])

    # ── Passwords don't match ─────────────────────────────

    def test_password_mismatch(self):
        form = SignupForm(data=self._form_data(
            password1='Strong@Pass1', password2='Different@Pass2'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertIn('do not match', form.errors['password2'][0])

    # ── Similarity to username ────────────────────────────

    def test_password_similar_to_username(self):
        form = SignupForm(data=self._form_data(
            username='alexander',
            password1='Alex@nder1!',
            password2='Alex@nder1!',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('too similar to your username', str(form.errors))

    # ── Similarity to email ───────────────────────────────

    def test_password_similar_to_email(self):
        form = SignupForm(data=self._form_data(
            email='charlotte@example.com',
            password1='Charl0tte!X',
            password2='Charl0tte!X',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('too similar to your email', str(form.errors))

    # ── Short username skips similarity check ─────────────

    def test_short_username_skips_similarity(self):
        form = SignupForm(data=self._form_data(
            username='abc',
            password1='Abc@1234!',
            password2='Abc@1234!',
        ))
        self.assertTrue(form.is_valid())

    # ── Short email local part skips similarity check ─────

    def test_short_email_local_skips_similarity(self):
        form = SignupForm(data=self._form_data(
            email='ab@example.com',
            password1='Ab@12345!',
            password2='Ab@12345!',
        ))
        self.assertTrue(form.is_valid())

    # ── Duplicate email ───────────────────────────────────

    def test_duplicate_email(self):
        User.objects.create_user(
            username='existing', email='taken@example.com', password='Pass1234!'
        )
        form = SignupForm(data=self._form_data(email='taken@example.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already exists', form.errors['email'][0])

    # ── clean() with invalid password1 (None) ─────────────

    def test_clean_skips_similarity_when_password1_invalid(self):
        """If password1 fails validation, clean() should not run similarity."""
        form = SignupForm(data=self._form_data(
            password1='short',
            password2='short',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)


class LoginFormTests(TestCase):
    """Tests for the LoginForm widget configuration."""

    def test_form_has_bootstrap_classes(self):
        form = LoginForm()
        self.assertIn('form-control', form.fields['username'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['password'].widget.attrs['class'])

    def test_form_has_placeholders(self):
        form = LoginForm()
        self.assertEqual(form.fields['username'].widget.attrs['placeholder'], 'Username')
        self.assertEqual(form.fields['password'].widget.attrs['placeholder'], 'Password')
