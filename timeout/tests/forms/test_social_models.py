from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from timeout.models import Post, Comment, Like, Bookmark

User = get_user_model()


class SocialModelsTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="pass123")
        self.u1 = User.objects.create_user(username="u1", password="pass123")
        self.u2 = User.objects.create_user(username="u2", password="pass123")

        self.public_post = Post.objects.create(
            author=self.author,
            content="public",
            privacy=Post.Privacy.PUBLIC,
        )
        self.private_post = Post.objects.create(
            author=self.author,
            content="followers only",
            privacy=Post.Privacy.FOLLOWERS_ONLY,
        )

    def test_post_like_count_and_is_liked_by(self):
        self.assertEqual(self.public_post.get_like_count(), 0)
        self.assertFalse(self.public_post.is_liked_by(self.u1))

        Like.objects.create(user=self.u1, post=self.public_post)
        self.assertEqual(self.public_post.get_like_count(), 1)
        self.assertTrue(self.public_post.is_liked_by(self.u1))

    def test_like_unique_together(self):
        Like.objects.create(user=self.u1, post=self.public_post)
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.u1, post=self.public_post)

    def test_bookmark_unique_together_and_is_bookmarked_by(self):
        self.assertFalse(self.public_post.is_bookmarked_by(self.u1))
        Bookmark.objects.create(user=self.u1, post=self.public_post)
        self.assertTrue(self.public_post.is_bookmarked_by(self.u1))

        with self.assertRaises(IntegrityError):
            Bookmark.objects.create(user=self.u1, post=self.public_post)

    def test_comment_reply_helpers_and_delete_permission(self):
        c1 = Comment.objects.create(post=self.public_post, author=self.u1, content="parent")
        self.assertFalse(c1.is_reply())
        self.assertEqual(c1.get_reply_count(), 0)

        reply = Comment.objects.create(post=self.public_post, author=self.u2, content="reply", parent=c1)
        self.assertTrue(reply.is_reply())
        self.assertEqual(c1.get_reply_count(), 1)

        # can_delete: author or staff
        self.assertTrue(c1.can_delete(self.u1))
        self.assertFalse(c1.can_delete(self.u2))
        self.u2.is_staff = True
        self.u2.save()
        self.assertTrue(c1.can_delete(self.u2))

    def test_post_can_delete(self):
        self.assertTrue(self.public_post.can_delete(self.author))
        self.assertFalse(self.public_post.can_delete(self.u1))
        self.u1.is_staff = True
        self.u1.save()
        self.assertTrue(self.public_post.can_delete(self.u1))

    def test_post_can_view_public(self):
        self.assertTrue(self.public_post.can_view(self.u1))

    def test_post_can_view_followers_only(self):
        self.assertFalse(self.private_post.can_view(self.u1))

        self.u1.following.add(self.author)
        self.assertTrue(self.private_post.can_view(self.u1))

        self.assertTrue(self.private_post.can_view(self.author))