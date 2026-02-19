from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Event(models.Model):
    """Calendar event model."""

    class EventType(models.TextChoices):
        """Event type choices."""
        DEADLINE = 'deadline', 'Deadline'
        EXAM = 'exam', 'Exam'
        CLASS = 'class', 'Class'
        MEETING = 'meeting', 'Meeting'
        STUDY_SESSION = 'study_session', 'Study Session'
        OTHER = 'other', 'Other'

    class EventStatus(models.TextChoices):
        """Event status choices."""
        UPCOMING = 'upcoming', 'Upcoming'
        ONGOING = 'ongoing', 'Ongoing'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    class EventPriority(models.TextChoices):
        """Event priority choices."""
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class EventRecurrence(models.TextChoices):
        """Event recurrence choices."""
        NONE = 'none', 'None'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER
    )

    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.UPCOMING
    )

    recurrence = models.CharField(
        max_length=20,
        choices=EventRecurrence.choices,
        default=EventRecurrence.NONE
    )

    allow_conflict = models.BooleanField(
        default=False,
        help_text='if true, event overlaps with others'
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    is_all_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(
                fields=['creator', '-start_datetime'],
                name='timeout_eve_creator_idx'
            ),
            models.Index(
                fields=['start_datetime'],
                name='timeout_eve_start_idx'
            ),
        ]

    def clean(self):
        """
        Prevent overlapping events for the same user unless allowed.
        """

        # 1️⃣ Validate time range
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("End time must be after start time.")

        # 2️⃣ Allow certain types to overlap automatically
        overlap_allowed_types = [
            self.EventType.DEADLINE,  # keep or change as you like
        ]

        if self.event_type in overlap_allowed_types:
            return

        # 3️⃣ Allow override checkbox
        if self.allow_conflict:
            return

        # 4️⃣ Ignore cancelled events
        if self.status == self.EventStatus.CANCELLED:
            return

        overlapping_events = Event.objects.filter(
            creator=self.creator,
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        ).exclude(pk=self.pk)

        if overlapping_events.exists():
            conflict = overlapping_events.first()
            raise ValidationError(
                f'This event conflicts with "{conflict.title}" '
                f'({conflict.start_datetime:%d %b %H:%M} - '
                f'{conflict.end_datetime:%H:%M}). '
                f'Tick "Override conflict" to allow it.'
            )



    @property
    def is_past(self):
        """Check if the event has already occurred."""
        from django.utils import timezone
        return self.end_datetime < timezone.now()

    @property
    def is_ongoing(self):
        """Check if the event is currently happening."""
        from django.utils import timezone
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    @property
    def is_upcoming(self):
        """Check if the event is in the future."""
        from django.utils import timezone
        return self.start_datetime > timezone.now()

    def __str__(self):
        return f"{self.title} ({self.start_datetime.date()})"
