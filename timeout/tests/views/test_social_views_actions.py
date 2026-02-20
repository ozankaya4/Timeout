import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from timeout.models import Post, Like, Bookmark, Comment

User = get_user_model()


class SocialViewsActionsTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="pass123")
        self.other = User.objects.create_user(username="other", password="pass123")

        self.post_public = Post.objects.create(
            author=self.author, content="pub", privacy=Post.Privacy.PUBLIC
        )
        self.post_private = Post.objects.create(
            author=self.author, content="priv", privacy=Post.Privacy.FOLLOWERS_ONLY
        )

    def login(self, user):
        ok = self.client.login(username=user.username, password="pass123")
        self.assertTrue(ok)

    def test_create_post(self):
        self.login(self.author)
        res = self.client.post(
            reverse("create_post"),
            data={"content": "new", "privacy": Post.Privacy.PUBLIC}
        )
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Post.objects.filter(author=self.author, content="new").exists())

    def test_delete_post_permission_denied_for_non_author(self):
        self.login(self.other)
        res = self.client.post(reverse("delete_post", args=[self.post_public.id]))
        self.assertEqual(res.status_code, 403)
        self.assertTrue(Post.objects.filter(id=self.post_public.id).exists())

    def test_delete_post_ok_for_author(self):
        self.login(self.author)
        res = self.client.post(reverse("delete_post", args=[self.post_public.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Post.objects.filter(id=self.post_public.id).exists())

    def test_like_toggle_public_post(self):
        self.login(self.other)
        url = reverse("like_post", args=[self.post_public.id])

        res1 = self.client.post(url)
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.content)
        self.assertTrue(data1["liked"])
        self.assertEqual(Like.objects.filter(user=self.other, post=self.post_public).count(), 1)

        res2 = self.client.post(url)
        data2 = json.loads(res2.content)
        self.assertFalse(data2["liked"])
        self.assertEqual(Like.objects.filter(user=self.other, post=self.post_public).count(), 0)

    def test_bookmark_toggle_public_post(self):
        self.login(self.other)
        url = reverse("bookmark_post", args=[self.post_public.id])

        res1 = self.client.post(url)
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.content)
        self.assertTrue(data1["bookmarked"])
        self.assertEqual(Bookmark.objects.filter(user=self.other, post=self.post_public).count(), 1)

        res2 = self.client.post(url)
        data2 = json.loads(res2.content)
        self.assertFalse(data2["bookmarked"])
        self.assertEqual(Bookmark.objects.filter(user=self.other, post=self.post_public).count(), 0)

    def test_like_private_post_forbidden_if_not_follower(self):
        self.login(self.other)
        res = self.client.post(reverse("like_post", args=[self.post_private.id]))
        self.assertEqual(res.status_code, 403)

    def test_like_private_post_ok_if_follower(self):
        self.other.following.add(self.author)
        self.login(self.other)
        res = self.client.post(reverse("like_post", args=[self.post_private.id]))
        self.assertEqual(res.status_code, 200)

    def test_add_comment_and_reply(self):
        self.login(self.other)

        # add comment
        res1 = self.client.post(
            reverse("add_comment", args=[self.post_public.id]),
            data={"content": "first"}
        )
        self.assertEqual(res1.status_code, 302)
        c1 = Comment.objects.get(post=self.post_public, author=self.other, content="first")

        # reply
        res2 = self.client.post(
            reverse("add_comment", args=[self.post_public.id]),
            data={"content": "reply", "parent_id": str(c1.id)}
        )
        self.assertEqual(res2.status_code, 302)
        reply = Comment.objects.get(post=self.post_public, author=self.other, content="reply")
        self.assertEqual(reply.parent_id, c1.id)

    def test_follow_toggle(self):
        self.login(self.other)
        url = reverse("follow_user", args=[self.author.username])

        res1 = self.client.post(url)
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.content)
        self.assertTrue(data1["following"])
        self.assertTrue(self.other.following.filter(id=self.author.id).exists())

        res2 = self.client.post(url)
        data2 = json.loads(res2.content)
        self.assertFalse(data2["following"])
        self.assertFalse(self.other.following.filter(id=self.author.id).exists())

    def test_follow_self_rejected(self):
        self.login(self.author)
        url = reverse("follow_user", args=[self.author.username])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 400)
    

    def test_feed_discover_tab(self):
        self.login(self.other)
        res = self.client.get(reverse("social_feed") + "?tab=discover")
        self.assertEqual(res.status_code, 200)

    def test_create_post_invalid(self):
        self.login(self.author)
        res = self.client.post(
            reverse("create_post"),
            data={"content": "", "privacy": Post.Privacy.PUBLIC},
        )
        self.assertEqual(res.status_code, 302)

    def test_bookmark_private_post_forbidden_if_not_follower(self):
        self.login(self.other) 
        res = self.client.post(reverse("bookmark_post", args=[self.post_private.id]))
        self.assertEqual(res.status_code, 403)

    def test_bookmarks_view_ok(self):
        self.login(self.other)
        res = self.client.get(reverse("bookmarks"))
        self.assertEqual(res.status_code, 200)

    def test_add_comment_forbidden_on_private_post_if_not_follower(self):
        self.login(self.other)
        res = self.client.post(
            reverse("add_comment", args=[self.post_private.id]),
            data={"content": "hi"},
        )
        self.assertEqual(res.status_code, 403)

    def test_add_comment_invalid_form(self):
        self.other.following.add(self.author)  
        self.login(self.other)
        res = self.client.post(
            reverse("add_comment", args=[self.post_private.id]),
            data={"content": ""},  
        )
        self.assertEqual(res.status_code, 302)

    def test_user_profile_view_ok(self):
        self.other.following.add(self.author)
        self.login(self.other)
        res = self.client.get(reverse("user_profile", args=[self.author.username]))
        self.assertEqual(res.status_code, 200)
    
    def test_feed_unknown_tab_defaults(self):
        self.login(self.other)
        res = self.client.get(reverse("social_feed") + "?tab=wtf")
        self.assertEqual(res.status_code, 200)