from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.contrib.auth.models import AnonymousUser

from timeout.models import Post, Comment, Like, Bookmark

User = get_user_model()


class SocialModelsTest(TestCase):
    """
    Coverage-focused tests for social-related model helpers and constraints.

    These tests verify:
    - helper methods (counts, permission checks, visibility rules)
    - unique constraints (Like/Bookmark)
    - __str__ representations
    - authenticated vs anonymous branches
    """

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

    # Covers get_like_count() and is_liked_by()
    def test_post_like_count_and_is_liked_by(self):
        self.assertEqual(self.public_post.get_like_count(), 0)
        self.assertFalse(self.public_post.is_liked_by(self.u1))

        Like.objects.create(user=self.u1, post=self.public_post)
        self.assertEqual(self.public_post.get_like_count(), 1)
        self.assertTrue(self.public_post.is_liked_by(self.u1))

    # Ensures Like model enforces unique(user, post)
    def test_like_unique_together(self):
        Like.objects.create(user=self.u1, post=self.public_post)
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.u1, post=self.public_post)

    # Covers is_bookmarked_by() and unique constraint
    def test_bookmark_unique_together_and_is_bookmarked_by(self):
        self.assertFalse(self.public_post.is_bookmarked_by(self.u1))
        Bookmark.objects.create(user=self.u1, post=self.public_post)
        self.assertTrue(self.public_post.is_bookmarked_by(self.u1))

        with self.assertRaises(IntegrityError):
            Bookmark.objects.create(user=self.u1, post=self.public_post)

    # Covers reply helpers and delete permission logic
    def test_comment_reply_helpers_and_delete_permission(self):
        c1 = Comment.objects.create(post=self.public_post, author=self.u1, content="parent")
        self.assertFalse(c1.is_reply())
        self.assertEqual(c1.get_reply_count(), 0)

        reply = Comment.objects.create(post=self.public_post, author=self.u2, content="reply", parent=c1)
        self.assertTrue(reply.is_reply())
        self.assertEqual(c1.get_reply_count(), 1)

        # can_delete: comment author or staff
        self.assertTrue(c1.can_delete(self.u1))
        self.assertFalse(c1.can_delete(self.u2))

        self.u2.is_staff = True
        self.u2.save()
        self.assertTrue(c1.can_delete(self.u2))

    # Covers Post.can_delete() permission branches
    def test_post_can_delete(self):
        self.assertTrue(self.public_post.can_delete(self.author))
        self.assertFalse(self.public_post.can_delete(self.u1))

        self.u1.is_staff = True
        self.u1.save()
        self.assertTrue(self.public_post.can_delete(self.u1))

    # Public posts should be visible to any authenticated user
    def test_post_can_view_public(self):
        self.assertTrue(self.public_post.can_view(self.u1))

    # Followers-only visibility logic
    def test_post_can_view_followers_only(self):
        self.assertFalse(self.private_post.can_view(self.u1))

        self.u1.following.add(self.author)
        self.assertTrue(self.private_post.can_view(self.u1))

        # Author should always see own post
        self.assertTrue(self.private_post.can_view(self.author))

    # Covers __str__ methods and anonymous branches
    def test_post_str_and_unauth_branches_and_comment_count(self):
        s = str(self.public_post)
        self.assertIn(self.author.username, s)

        anon = AnonymousUser()

        # Anonymous users cannot like/bookmark
        self.assertFalse(self.public_post.is_liked_by(anon))
        self.assertFalse(self.public_post.is_bookmarked_by(anon))

        Comment.objects.create(post=self.public_post, author=self.u1, content="c")
        self.assertEqual(self.public_post.get_comment_count(), 1)

        # Anonymous visibility and delete checks
        self.assertFalse(self.private_post.can_view(anon))
        self.assertFalse(self.public_post.can_delete(anon))

    # Covers Comment.__str__ and anonymous delete branch
    def test_comment_str_and_can_delete_unauth(self):
        c = Comment.objects.create(
            post=self.public_post,
            author=self.u1,
            content="x" * 40
        )
        self.assertIn(self.u1.username, str(c))

        anon = AnonymousUser()
        self.assertFalse(c.can_delete(anon))

    # Covers Like.__str__()
    def test_like_str(self):
        like = Like.objects.create(user=self.u1, post=self.public_post)
        self.assertIn("likes", str(like))

    # Covers Bookmark.__str__()
    def test_bookmark_str(self):
        bm = Bookmark.objects.create(user=self.u1, post=self.public_post)
        self.assertIn("bookmarked", str(bm))