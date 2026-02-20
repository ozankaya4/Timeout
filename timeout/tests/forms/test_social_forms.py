from django.test import TestCase
from django.contrib.auth import get_user_model

from timeout.forms import PostForm, CommentForm
from timeout.models import Post

User = get_user_model()


class SocialFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass123")

    def test_post_form_valid_minimal(self):
        form = PostForm(data={"content": "hi", "privacy": Post.Privacy.PUBLIC}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_post_form_event_optional(self):
        form = PostForm(data={"content": "hi", "privacy": Post.Privacy.PUBLIC, "event": ""}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_comment_form_valid(self):
        form = CommentForm(data={"content": "nice"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_comment_form_reject_too_long(self):
        form = CommentForm(data={"content": "a" * 1001})
        self.assertFalse(form.is_valid())