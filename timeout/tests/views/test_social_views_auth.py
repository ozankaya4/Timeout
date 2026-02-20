from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from timeout.models import Post

User = get_user_model()


class SocialViewsAuthTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass123")
        self.post = Post.objects.create(author=self.user, content="x", privacy=Post.Privacy.PUBLIC)

    def test_feed_requires_login(self):
        res = self.client.get(reverse("social_feed"))
        self.assertIn(res.status_code, (302, 401, 403))

    def test_bookmarks_requires_login(self):
        res = self.client.get(reverse("bookmarks"))
        self.assertIn(res.status_code, (302, 401, 403))

    def test_like_requires_login(self):
        res = self.client.post(reverse("like_post", args=[self.post.id]))
        self.assertIn(res.status_code, (302, 401, 403))