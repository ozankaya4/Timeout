from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from timeout.models import Post, Like, Comment, Bookmark
from timeout.services import FeedService

User = get_user_model()


class FeedServiceTest(TestCase):
    """
    Tests for FeedService query logic.

    - following feed vs discover feed filtering
    - privacy rules (public vs followers-only)
    - user posts visibility depending on viewer relationship
    - bookmarks filtering
    - anonymous user edge cases (should return empty querysets)
    """

    def setUp(self):
        # Users: me follows A, does not follow B
        self.me = User.objects.create_user(username="me", password="pass123")
        self.a = User.objects.create_user(username="a", password="pass123")
        self.b = User.objects.create_user(username="b", password="pass123")

        self.me.following.add(self.a)

        # A has both public + followers-only posts
        self.a_pub = Post.objects.create(author=self.a, content="a public", privacy=Post.Privacy.PUBLIC)
        self.a_priv = Post.objects.create(author=self.a, content="a private", privacy=Post.Privacy.FOLLOWERS_ONLY)

        # B has a public post (should appear in discover, not in following feed)
        self.b_pub = Post.objects.create(author=self.b, content="b public", privacy=Post.Privacy.PUBLIC)

        # Engagement by me on B's post
        Like.objects.create(user=self.me, post=self.b_pub)
        Comment.objects.create(author=self.me, post=self.b_pub, content="wow")
        Bookmark.objects.create(user=self.me, post=self.b_pub)

    # Following feed should include followed users' posts (including followers-only) and my own posts
    def test_following_feed_includes_followed_and_own(self):
        feed = FeedService.get_following_feed(self.me)
        self.assertIn(self.a_pub, feed)
        self.assertIn(self.a_priv, feed)
        self.assertNotIn(self.b_pub, feed)

        my_post = Post.objects.create(author=self.me, content="mine", privacy=Post.Privacy.PUBLIC)
        feed2 = FeedService.get_following_feed(self.me)
        self.assertIn(my_post, feed2)

    # Discover feed should exclude followed users and my own posts, but include other users' public posts
    def test_discover_feed_excludes_followed_and_own(self):
        my_public = Post.objects.create(author=self.me, content="me pub", privacy=Post.Privacy.PUBLIC)
        discover = list(FeedService.get_discover_feed(self.me))
        self.assertNotIn(my_public, discover)
        self.assertNotIn(self.a_pub, discover)
        self.assertIn(self.b_pub, discover)

    # Discover feed must only contain public posts (no followers-only)
    def test_discover_feed_only_public(self):
        Post.objects.create(author=self.b, content="b private", privacy=Post.Privacy.FOLLOWERS_ONLY)
        discover = list(FeedService.get_discover_feed(self.me))
        self.assertTrue(all(p.privacy == Post.Privacy.PUBLIC for p in discover))

    # Viewing a user's posts should respect privacy: non-followers shouldn't see followers-only
    def test_user_posts_privacy_filtered(self):
        viewer = User.objects.create_user(username="viewer", password="pass123")
        posts = FeedService.get_user_posts(self.a, viewer)
        self.assertIn(self.a_pub, posts)
        self.assertNotIn(self.a_priv, posts)

    # Bookmarked posts should respect privacy rules
    def test_bookmarked_posts_privacy_filtered(self):
        posts = FeedService.get_bookmarked_posts(self.me)
        self.assertIn(self.b_pub, posts)

        b_private = Post.objects.create(
            author=self.b,
            content="b private",
            privacy=Post.Privacy.FOLLOWERS_ONLY,
        )
        Bookmark.objects.create(user=self.me, post=b_private)

        posts_after = FeedService.get_bookmarked_posts(self.me)
        self.assertNotIn(b_private, posts_after)

        self.me.following.add(self.b)
        posts_after_follow = FeedService.get_bookmarked_posts(self.me)
        self.assertIn(b_private, posts_after_follow)

    # Anonymous users should get empty results for following feed
    def test_following_feed_unauth_returns_empty_queryset(self):
        anon = AnonymousUser()
        qs = FeedService.get_following_feed(anon)
        self.assertEqual(qs.count(), 0)

    # Anonymous users should get empty results for bookmarks
    def test_bookmarked_posts_unauth_returns_empty_queryset(self):
        anon = AnonymousUser()
        qs = FeedService.get_bookmarked_posts(anon)
        self.assertEqual(qs.count(), 0)