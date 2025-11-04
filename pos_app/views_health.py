"""
Health check view for monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint for monitoring and load balancers
    Returns 200 if all systems are operational
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    status_code = 200
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['checks']['database'] = 'error'
        health_status['status'] = 'unhealthy'
        status_code = 503
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error'
            health_status['status'] = 'degraded'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status['checks']['cache'] = 'error'
        health_status['status'] = 'degraded'
    
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check - ensures app is ready to serve traffic
    """
    from django.apps import apps
    
    ready_status = {
        'ready': True,
        'checks': {}
    }
    status_code = 200
    
    # Check if all apps are loaded
    try:
        if apps.ready:
            ready_status['checks']['apps'] = 'ok'
        else:
            ready_status['checks']['apps'] = 'not_ready'
            ready_status['ready'] = False
            status_code = 503
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        ready_status['checks']['apps'] = 'error'
        ready_status['ready'] = False
        status_code = 503
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        ready_status['checks']['database'] = 'ok'
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        ready_status['checks']['database'] = 'error'
        ready_status['ready'] = False
        status_code = 503
    
    return JsonResponse(ready_status, status=status_code)
