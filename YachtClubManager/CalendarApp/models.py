from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from ckeditor.fields import RichTextField

ClubUser = get_user_model()


class EventCategory(models.Model):
    """Category for organizing events (e.g., Racing, Social, Training, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code for calendar display')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Event Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    """Calendar event/activity for the Yacht Club"""
    
    REGISTRATION_STATUS_CHOICES = [
        ('not_required', 'Not Required'),
        ('recommended', 'Recommended'),
        ('required', 'Required'),
        ('required_by_close_date', 'Required By Close Date'),
        ('admins_contacts_only', 'Admins / Event Contacts Only'),
        ('temporarily_unavailable', 'Temporarily Unavailable'),
        ('closed', 'Closed'),
        ('external', 'External'),
    ]
    
    REGISTRANT_LIST_VISIBILITY_CHOICES = [
        ('none', 'None'),
        ('viewer_public', 'Viewer/Public'),
        ('members', 'Members'),
        ('registered_members_only', 'Registered Members Only'),
    ]
    
    title = models.CharField(max_length=200)
    short_description = models.TextField(max_length=500, help_text='Brief description of the event')
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    formatted_description = RichTextField(blank=True, null=True, help_text='Full formatted description with rich text')
    registration_status = models.CharField(
        max_length=30,
        choices=REGISTRATION_STATUS_CHOICES,
        default='not_required',
        help_text='Registration status for this event'
    )
    registration_open_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional date and time when registration AUTOMATICALLY opens for REGISTRATIONS on this event'
    )
    registrant_list_visibility = models.CharField(
        max_length=30,
        choices=REGISTRANT_LIST_VISIBILITY_CHOICES,
        default='none',
        help_text='Who can view the list of registrants for this event'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['start_datetime', 'end_datetime']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        return reverse('calendar:event_detail', kwargs={'pk': self.pk})

    @property
    def duration(self):
        """Calculate the duration of the event"""
        return self.end_datetime - self.start_datetime

    @property
    def is_all_day(self):
        """Check if event spans a full day"""
        from datetime import time
        return self.duration.days >= 1 and self.start_datetime.time() == self.end_datetime.time() == time.min

    def get_primary_contact(self):
        """Get the primary contact for this event"""
        return self.event_contacts.filter(is_primary=True).first()

    def get_contacts(self):
        """Get all contacts ordered by primary first, then by name"""
        return self.event_contacts.all().order_by('-is_primary', 'member__last_name', 'member__first_name')


class EventContact(models.Model):
    """Association between an Event and a ClubUser with contact responsibilities"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_contacts')
    member = models.ForeignKey(ClubUser, on_delete=models.CASCADE, related_name='event_contacts')
    is_primary = models.BooleanField(default=False, help_text='Designates this contact as the primary contact')
    responsibilities = models.TextField(blank=True, help_text='Responsibilities for this event')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['event', 'member']]
        ordering = ['-is_primary', 'member__last_name', 'member__first_name']

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.member.get_full_name()} - {self.event.title}{primary}"

    def save(self, *args, **kwargs):
        # Ensure only one primary contact per event
        if self.is_primary:
            EventContact.objects.filter(event=self.event, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class EventActionLog(models.Model):
    """Log of actions taken on events by editors and admins"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    ]
    
    event = models.ForeignKey(
        Event, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='action_logs',
        help_text='Event may be NULL if deleted'
    )
    user = models.ForeignKey(
        ClubUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='event_actions',
        help_text='User who performed the action'
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    event_title = models.CharField(max_length=200, help_text='Snapshot of event title at time of action')
    event_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Additional event data at time of action (for deleted events)'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'Event Action Log'
        verbose_name_plural = 'Event Action Logs'
    
    def __str__(self):
        event_ref = self.event.title if self.event else self.event_title
        user_name = self.user.get_full_name() if self.user else "Unknown User"
        return f"{user_name} {self.get_action_display()} '{event_ref}' on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
