"""
Health check and monitoring views for system stability
"""
import logging
import psutil
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

logger = logging.getLogger(__name__)


@require_GET
@never_cache
def health_check(request):
    """
    Comprehensive health check endpoint for monitoring
    Returns 200 if system is healthy, 503 if any critical service is down
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    is_healthy = True
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = {
            'status': 'ok',
            'message': 'Database connection successful'
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['checks']['database'] = {
            'status': 'error',
            'message': str(e)
        }
        is_healthy = False
    
    # Check disk space
    try:
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        health_status['checks']['disk_space'] = {
            'status': 'ok' if disk_percent < 90 else 'warning',
            'used_percent': disk_percent,
            'available_gb': round(disk.free / (1024**3), 2)
        }
        if disk_percent >= 95:
            is_healthy = False
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        health_status['checks']['disk_space'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check memory usage
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        health_status['checks']['memory'] = {
            'status': 'ok' if memory_percent < 90 else 'warning',
            'used_percent': memory_percent,
            'available_gb': round(memory.available / (1024**3), 2)
        }
        if memory_percent >= 95:
            is_healthy = False
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        health_status['checks']['memory'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check CPU usage
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status['checks']['cpu'] = {
            'status': 'ok' if cpu_percent < 90 else 'warning',
            'used_percent': cpu_percent
        }
    except Exception as e:
        logger.error(f"CPU check failed: {e}")
        health_status['checks']['cpu'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Set overall status
    if not is_healthy:
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status, status=200)


@require_GET
@never_cache
def readiness_check(request):
    """
    Simple readiness check for load balancers
    Returns 200 if app is ready to receive traffic
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'ready'}, status=200)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'status': 'not ready',
            'error': str(e)
        }, status=503)


@require_GET
@never_cache
def liveness_check(request):
    """
    Simple liveness check for container orchestration
    Returns 200 if app is alive
    """
    return JsonResponse({'status': 'alive'}, status=200)
