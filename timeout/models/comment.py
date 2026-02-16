from django.conf import settings
from django.db import models


class Comment(models.Model):
    """Threaded comments for posts."""

    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        preview = self.content[:30]
        return f'{self.author.username}: {preview}...'

    def is_reply(self):
        """Check if this comment is a reply to another."""
        return self.parent is not None

    def get_reply_count(self):
        """Return count of direct replies."""
        return self.replies.count()

    def can_delete(self, user):
        """Check if user can delete this comment."""
        if not user.is_authenticated:
            return False
        return self.author == user or user.is_staff
