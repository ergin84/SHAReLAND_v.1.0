"""
Audit logging models for tracking user operations across the application.
Records all create, update, and delete operations with user, timestamp, and change details.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class AuditLog(models.Model):
    """
    Audit log model to track all user operations in the system.
    Records what was changed, by whom, and when.
    """
    
    # Operation types
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    VIEW = 'VIEW'
    
    OPERATION_CHOICES = [
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (VIEW, 'View'),
    ]
    
    # Log entry details
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    model_name = models.CharField(max_length=100, help_text="Name of the model that was modified")
    object_id = models.CharField(max_length=255, help_text="ID of the object that was modified")
    object_str = models.CharField(max_length=500, blank=True, help_text="String representation of the object")
    
    # Change tracking
    changes = models.JSONField(default=dict, blank=True, help_text="JSON object tracking what changed")
    old_values = models.JSONField(default=dict, blank=True, help_text="Previous field values")
    new_values = models.JSONField(default=dict, blank=True, help_text="New field values")
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
            models.Index(fields=['operation', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.operation} {self.model_name} ({self.object_id}) by {self.user} at {self.timestamp}"
    
    @property
    def get_changes_display(self):
        """Get human-readable changes display"""
        if not self.changes:
            return "No changes recorded"
        
        change_list = []
        for field, (old, new) in self.changes.items():
            change_list.append(f"{field}: '{old}' → '{new}'")
        return ", ".join(change_list)
    
    @property
    def get_duration(self):
        """Get time elapsed since this log entry"""
        from django.utils.timezone import now
        delta = now() - self.timestamp
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"


class AccessLog(models.Model):
    """
    Simple access log to track page visits by users.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    page = models.CharField(max_length=255)
    view_name = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'access_log'
        verbose_name = 'Access Log'
        verbose_name_plural = 'Access Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} accessed {self.page} at {self.timestamp}"
