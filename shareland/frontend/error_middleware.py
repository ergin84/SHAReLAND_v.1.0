"""
Error handling middleware for robust application stability
"""
import logging
import sys
import traceback
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import Http404

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """
    Middleware to catch and handle all unhandled exceptions gracefully
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)

    def handle_exception(self, request, exception):
        """Handle exceptions based on their type"""
        
        # Log the full traceback
        exc_info = sys.exc_info()
        logger.error(
            f"Unhandled exception in request {request.path}",
            exc_info=exc_info,
            extra={
                'request': request,
                'user': request.user if hasattr(request, 'user') else None,
            }
        )

        # Handle different exception types
        if isinstance(exception, Http404):
            return self.handle_404(request)
        elif isinstance(exception, PermissionDenied):
            return self.handle_403(request)
        elif isinstance(exception, SuspiciousOperation):
            return self.handle_400(request)
        else:
            return self.handle_500(request, exception)

    def handle_400(self, request):
        """Handle bad request errors"""
        if request.accepts('application/json'):
            return JsonResponse({
                'error': 'Bad Request',
                'message': 'The request could not be understood or was missing required parameters.'
            }, status=400)
        return render(request, 'errors/400.html', status=400)

    def handle_403(self, request):
        """Handle permission denied errors"""
        if request.accepts('application/json'):
            return JsonResponse({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource.'
            }, status=403)
        return render(request, 'errors/403.html', status=403)

    def handle_404(self, request):
        """Handle not found errors"""
        if request.accepts('application/json'):
            return JsonResponse({
                'error': 'Not Found',
                'message': 'The requested resource was not found.'
            }, status=404)
        return render(request, 'errors/404.html', status=404)

    def handle_500(self, request, exception):
        """Handle server errors"""
        if request.accepts('application/json'):
            error_data = {
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }
            if settings.DEBUG:
                error_data['debug'] = {
                    'exception': str(exception),
                    'traceback': traceback.format_exc()
                }
            return JsonResponse(error_data, status=500)
        
        context = {}
        if settings.DEBUG:
            context['exception'] = exception
            context['traceback'] = traceback.format_exc()
        
        return render(request, 'errors/500.html', context, status=500)


class RateLimitMiddleware:
    """
    Simple rate limiting middleware to prevent abuse
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}  # In production, use Redis or Memcached
        
    def __call__(self, request):
        # Skip rate limiting for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Check rate limit (100 requests per minute per IP)
        if self.is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            if request.accepts('application/json'):
                return JsonResponse({
                    'error': 'Rate Limit Exceeded',
                    'message': 'Too many requests. Please try again later.'
                }, status=429)
            return render(request, 'errors/429.html', status=429)
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, ip):
        """Check if IP has exceeded rate limit"""
        import time
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        self.requests = {
            k: [t for t in v if current_time - t < 60]
            for k, v in self.requests.items()
        }
        
        # Check current IP
        if ip not in self.requests:
            self.requests[ip] = []
        
        self.requests[ip].append(current_time)
        
        # Rate limit: 100 requests per minute
        return len(self.requests[ip]) > 100
