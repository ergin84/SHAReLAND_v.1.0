"""
Middleware for logging user operations and access.
Captures request/response data for audit trail.
"""

import threading

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .audit_logging import get_client_ip, log_operation
from .audit_models import AccessLog
from .models import ArchaeologicalEvidence, Research, Site

# Thread-local storage for request object (used by signal handlers below)
_thread_locals = threading.local()


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
        response = self.get_response(request)

        if request.user.is_authenticated:
            try:
                path = request.path
                if any(logged_path in path for logged_path in self.logged_paths):
                    AccessLog.objects.create(
                        user=request.user,
                        page=path,
                        view_name=request.resolver_match.url_name if request.resolver_match else '',
                        ip_address=get_client_ip(request),
                    )
            except Exception:
                pass

        return response


# Signal handlers for model operations logging

@receiver(post_save, sender=Research)
def log_research_change(sender, instance, created, **kwargs):
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        log_operation(request.user, 'CREATE' if created else 'UPDATE', instance, request)


@receiver(pre_delete, sender=Research)
def log_research_delete(sender, instance, **kwargs):
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        log_operation(request.user, 'DELETE', instance, request)


@receiver(post_save, sender=Site)
def log_site_change(sender, instance, created, **kwargs):
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        log_operation(request.user, 'CREATE' if created else 'UPDATE', instance, request)


@receiver(pre_delete, sender=Site)
def log_site_delete(sender, instance, **kwargs):
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        log_operation(request.user, 'DELETE', instance, request)


@receiver(post_save, sender=ArchaeologicalEvidence)
def log_evidence_change(sender, instance, created, **kwargs):
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        log_operation(request.user, 'CREATE' if created else 'UPDATE', instance, request)


@receiver(pre_delete, sender=ArchaeologicalEvidence)
def log_evidence_delete(sender, instance, **kwargs):
    request = getattr(_thread_locals, 'request', None)
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        log_operation(request.user, 'DELETE', instance, request)


class RequestLoggingMiddleware:
    """Store request in thread-local for signal handlers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            # Always clean up to prevent stale request objects leaking between
            # requests on the same thread (common with Gunicorn sync workers).
            _thread_locals.request = None
        return response
