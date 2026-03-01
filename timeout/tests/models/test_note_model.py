from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from timeout.models import Note, Event

User = get_user_model()


class NoteModelTest(TestCase):
    """Tests for Note model fields, methods, and constraints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', password='pass123'
        )
        self.other = User.objects.create_user(
            username='other', password='pass123'
        )
        self.staff = User.objects.create_user(
            username='staff', password='pass123', is_staff=True
        )
        self.event = Event.objects.create(
            creator=self.user,
            title='Exam',
            event_type=Event.EventType.EXAM,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timezone.timedelta(hours=2),
        )
        self.note = Note.objects.create(
            owner=self.user,
            title='Study Plan for Exam',
            content='Review chapters 1-5',
            category=Note.Category.STUDY_PLAN,
            event=self.event,
        )

    def test_str_representation(self):
        result = str(self.note)
        self.assertIn(self.user.username, result)
        self.assertIn('Study Plan', result)

    def test_default_values(self):
        note = Note.objects.create(
            owner=self.user,
            title='Quick Note',
            content='Some content',
        )
        self.assertFalse(note.is_pinned)
        self.assertEqual(note.category, Note.Category.OTHER)

    def test_get_color_all_categories(self):
        expected = {
            'lecture': 'primary',
            'todo': 'danger',
            'study_plan': 'success',
            'personal': 'info',
            'other': 'secondary',
        }
        for category, color in expected.items():
            self.note.category = category
            self.assertEqual(self.note.get_color(), color)

    def test_get_color_unknown_returns_secondary(self):
        self.note.category = 'unknown'
        self.assertEqual(self.note.get_color(), 'secondary')

    def test_can_edit_owner_returns_true(self):
        self.assertTrue(self.note.can_edit(self.user))

    def test_can_edit_non_owner_returns_false(self):
        self.assertFalse(self.note.can_edit(self.other))

    def test_can_edit_anonymous_returns_false(self):
        self.assertFalse(self.note.can_edit(AnonymousUser()))

    def test_can_delete_owner_returns_true(self):
        self.assertTrue(self.note.can_delete(self.user))

    def test_can_delete_non_owner_returns_false(self):
        self.assertFalse(self.note.can_delete(self.other))

    def test_can_delete_staff_returns_true(self):
        self.assertTrue(self.note.can_delete(self.staff))

    def test_can_delete_anonymous_returns_false(self):
        self.assertFalse(self.note.can_delete(AnonymousUser()))

    def test_ordering_pinned_first(self):
        pinned = Note.objects.create(
            owner=self.user,
            title='Pinned Note',
            content='Important',
            is_pinned=True,
        )
        notes = list(Note.objects.filter(owner=self.user))
        self.assertEqual(notes[0], pinned)

    def test_event_set_null_on_delete(self):
        self.event.delete()
        self.note.refresh_from_db()
        self.assertIsNone(self.note.event)

    def test_category_choices(self):
        values = [c[0] for c in Note.Category.choices]
        self.assertIn('lecture', values)
        self.assertIn('todo', values)
        self.assertIn('study_plan', values)
        self.assertIn('personal', values)
        self.assertIn('other', values)
