from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.contrib.auth.models import AnonymousUser
from threading import current_thread
import logging
from django.utils import timezone
from .utils import summarize_text
from datetime import date

logger = logging.getLogger(__name__)

# Create your models here.

class User(AbstractUser):
    is_team_lead = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    invite_code = models.CharField(max_length=10, unique=True, default=uuid.uuid4)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name
    
    def is_creator(self, user):
        return self.creator == user

class Membership(models.Model):
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('member', 'Team Member'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"

class StandUpEntry(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    yesterday = models.TextField()
    today = models.TextField()
    blockers = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    yesterday_summary = models.TextField(blank=True, null=True)
    today_summary = models.TextField(blank=True, null=True)
    blockers_summary = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Stand-up entries"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username}'s entry for {self.date}"

    @property
    def can_edit(self):
        return self.user == current_thread().request.user

    @property
    def can_delete(self):
        return self.user == current_thread().request.user

class Standup(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('archived', 'Archived'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='standups')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='standups')
    date = models.DateField(default=timezone.now)
    yesterday = models.TextField()
    today = models.TextField()
    blockers = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add summary fields
    yesterday_summary = models.TextField(blank=True)
    today_summary = models.TextField(blank=True)
    blockers_summary = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['team', 'user', 'date']

    def __str__(self):
        return f"{self.team.name} - {self.user.username} - {self.date}"

    def save(self, *args, **kwargs):
        logger.info("Starting summary generation for standup entry")
        
        # Generate summaries if they don't exist
        if not self.yesterday_summary and self.yesterday:
            logger.info("Generating summary for yesterday's work")
            self.yesterday_summary = summarize_text(self.yesterday)
            logger.info(f"Generated yesterday summary: {self.yesterday_summary}")
            
        if not self.today_summary and self.today:
            logger.info("Generating summary for today's work")
            self.today_summary = summarize_text(self.today)
            logger.info(f"Generated today summary: {self.today_summary}")
            
        if not self.blockers_summary and self.blockers:
            logger.info("Generating summary for blockers")
            self.blockers_summary = summarize_text(self.blockers)
            logger.info(f"Generated blockers summary: {self.blockers_summary}")
            
        super().save(*args, **kwargs)

    @property
    def can_edit(self):
        # Allow editing within 24 hours of creation
        return (timezone.now() - self.created_at).total_seconds() < 86400

    @property
    def can_delete(self):
        # Allow deletion within 24 hours of creation
        return (timezone.now() - self.created_at).total_seconds() < 86400