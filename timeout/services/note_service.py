from django.db.models import Q

from timeout.models import Note


class NoteService:
    """Service for managing note query logic."""

    @staticmethod
    def get_user_notes(user):
        """Get all notes for a user, pinned first then newest."""
        if not user.is_authenticated:
            return Note.objects.none()
        return Note.objects.filter(
            owner=user
        ).select_related('event').order_by(
            '-is_pinned', '-created_at'
        )

    @staticmethod
    def get_notes_by_category(user, category):
        """Get notes for a user filtered by category."""
        if not user.is_authenticated:
            return Note.objects.none()
        return Note.objects.filter(
            owner=user,
            category=category,
        ).select_related('event').order_by(
            '-is_pinned', '-created_at'
        )

    @staticmethod
    def get_notes_for_event(user, event_id):
        """Get notes linked to a specific event."""
        if not user.is_authenticated:
            return Note.objects.none()
        return Note.objects.filter(
            owner=user,
            event_id=event_id,
        ).select_related('event').order_by(
            '-is_pinned', '-created_at'
        )

    @staticmethod
    def search_notes(user, query):
        """Search notes by title or content."""
        if not user.is_authenticated:
            return Note.objects.none()
        return Note.objects.filter(
            owner=user,
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('event').order_by(
            '-is_pinned', '-created_at'
        )
