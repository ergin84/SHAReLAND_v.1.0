"""
Middleware for logging user operations and access.
Captures request/response data for audit trail.
"""

from .audit_models import AccessLog, AuditLog
from .audit_logging import get_client_ip, get_user_agent
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Research, Site, ArchaeologicalEvidence


class AuditLoggingMiddleware:
    """
    Middleware to log user access and operations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logged_paths = [
            '/research/',
            '/site',
            '/evidence',
            '/create-research',
            'site_create',
            'evidence_create',
        ]
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Log page access for authenticated users
        if request.user.is_authenticated:
            try:
                path = request.path
                # Only log certain paths
                if any(logged_path in path for logged_path in self.logged_paths):
                    AccessLog.objects.create(
                        user=request.user,
                        page=path,
                        view_name=request.resolver_match.url_name if request.resolver_match else '',
                        ip_address=get_client_ip(request),
                    )
            except Exception as e:
                # Silently fail
                pass
        
        return response


# Signal handlers for model operations logging
@receiver(post_save, sender=Research)
def log_research_change(sender, instance, created, **kwargs):
    """Log research creation/update"""
    from django.core.handlers.wsgi import WSGIRequest
    from threading import local
    
    # Try to get user from thread-local storage
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        from .audit_logging import log_operation
        operation = 'CREATE' if created else 'UPDATE'
        log_operation(request.user, operation, instance, request)


@receiver(pre_delete, sender=Research)
def log_research_delete(sender, instance, **kwargs):
    """Log research deletion"""
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        from .audit_logging import log_operation
        log_operation(request.user, 'DELETE', instance, request)


@receiver(post_save, sender=Site)
def log_site_change(sender, instance, created, **kwargs):
    """Log site creation/update"""
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        from .audit_logging import log_operation
        operation = 'CREATE' if created else 'UPDATE'
        log_operation(request.user, operation, instance, request)


@receiver(pre_delete, sender=Site)
def log_site_delete(sender, instance, **kwargs):
    """Log site deletion"""
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        from .audit_logging import log_operation
        log_operation(request.user, 'DELETE', instance, request)


@receiver(post_save, sender=ArchaeologicalEvidence)
def log_evidence_change(sender, instance, created, **kwargs):
    """Log evidence creation/update"""
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        from .audit_logging import log_operation
        operation = 'CREATE' if created else 'UPDATE'
        log_operation(request.user, operation, instance, request)


@receiver(pre_delete, sender=ArchaeologicalEvidence)
def log_evidence_delete(sender, instance, **kwargs):
    """Log evidence deletion"""
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        from .audit_logging import log_operation
        log_operation(request.user, 'DELETE', instance, request)


# Thread-local storage for request object
import threading
_thread_locals = threading.local()


class RequestLoggingMiddleware:
    """Store request in thread-local for signal handlers"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response
