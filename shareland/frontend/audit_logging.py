"""
Audit logging utilities for tracking operations.
Provides functions to log create, update, and delete operations.
"""

from django.utils import timezone
from .audit_models import AuditLog
import json


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def log_operation(user, operation, model_instance, request=None, old_values=None, new_values=None):
    """
    Log a user operation to the audit log.
    
    Args:
        user: Django User instance who performed the operation
        operation: Type of operation (CREATE, UPDATE, DELETE, VIEW)
        model_instance: The model instance being operated on
        request: Optional HTTP request for IP and user agent
        old_values: Dict of old field values (for updates)
        new_values: Dict of new field values (for updates)
    """
    try:
        changes = {}
        if old_values and new_values:
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changes[key] = (str(old_values[key])[:100], str(new_values[key])[:100])
        
        ip_address = None
        user_agent = ''
        if request:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
        
        AuditLog.objects.create(
            user=user,
            operation=operation,
            model_name=model_instance.__class__.__name__,
            object_id=str(model_instance.pk),
            object_str=str(model_instance)[:500],
            changes=changes,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log silently to avoid breaking operations
        print(f"Error logging operation: {e}")


def log_model_change(sender, instance, created, request=None, **kwargs):
    """
    Signal handler to log model creation/update.
    Used with post_save signal.
    """
    # Skip if model hasn't been saved yet or is a special model
    if not instance.pk:
        return
    
    operation = 'CREATE' if created else 'UPDATE'
    
    # Try to get user from thread-local or request
    user = None
    if request and hasattr(request, 'user'):
        user = request.user if request.user.is_authenticated else None
    
    if user:
        log_operation(user, operation, instance, request)


def log_model_delete(sender, instance, request=None, **kwargs):
    """
    Signal handler to log model deletion.
    Used with pre_delete signal.
    """
    user = None
    if request and hasattr(request, 'user'):
        user = request.user if request.user.is_authenticated else None
    
    if user:
        log_operation(user, 'DELETE', instance, request)
