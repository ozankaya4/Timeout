from .user_admin import UserAdmin
from .social_admin import (
    EventAdmin,
    PostAdmin,
    CommentAdmin,
    LikeAdmin,
    BookmarkAdmin,
)
from .note_admin import NoteAdmin

__all__ = [
    'UserAdmin',
    'EventAdmin',
    'PostAdmin',
    'CommentAdmin',
    'LikeAdmin',
    'BookmarkAdmin',
    'NoteAdmin',
]
