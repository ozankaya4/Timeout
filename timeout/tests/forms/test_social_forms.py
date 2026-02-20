from django.test import TestCase
from django.contrib.auth import get_user_model

from timeout.forms import PostForm, CommentForm
from timeout.models import Post

User = get_user_model()


class SocialFormsTest(TestCase):
    """
    Coverage-focused tests for PostForm and CommentForm.

    These tests verify validation behaviour only.
    They do not test rendering or detailed error messages.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", password="pass123"
        )

    # Minimal valid post should pass validation
    def test_post_form_valid_minimal(self):
        form = PostForm(
            data={"content": "hi", "privacy": Post.Privacy.PUBLIC},
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # Event field is optional and can be blank
    def test_post_form_event_optional_blank_ok(self):
        form = PostForm(
            data={"content": "hi", "privacy": Post.Privacy.PUBLIC, "event": ""},
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # Form should not crash when user=None is provided
    def test_post_form_init_without_user_does_not_crash(self):
        form = PostForm(
            data={"content": "hi", "privacy": Post.Privacy.PUBLIC},
            user=None,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # Valid comment content should pass validation
    def test_comment_form_valid(self):
        form = CommentForm(data={"content": "nice"})
        self.assertTrue(form.is_valid(), form.errors)

    # Comment exceeding max length should fail validation
    def test_comment_form_reject_too_long(self):
        form = CommentForm(data={"content": "a" * 1001})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)