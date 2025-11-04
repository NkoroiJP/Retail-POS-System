from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add custom attributes to request for role checking
        if request.user.is_authenticated:
            request.is_director = request.user.role == 'director'
            request.is_admin = request.user.role == 'admin'
            request.is_manager = request.user.role == 'manager'
            request.is_staff = request.user.role == 'staff'
            request.is_store_manager = request.user.role == 'manager' and request.user.store
        else:
            request.is_director = False
            request.is_admin = False
            request.is_manager = False
            request.is_staff = False
            request.is_store_manager = False

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # This method is called just before Django calls the view
        # We can add more specific permission checks here if needed
        pass


class AuditLogMiddleware:
    """Middleware to log important user actions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log authentication events
        if request.user.is_authenticated and request.path in ['/login/', '/logout/']:
            self._log_auth_event(request, response)
        
        return response
    
    def _log_auth_event(self, request, response):
        """Log login/logout events"""
        try:
            from .models_audit import AuditLog
            
            action = 'login' if 'login' in request.path else 'logout'
            
            if response.status_code in [200, 302]:  # Success
                AuditLog.objects.create(
                    user=request.user,
                    action=action,
                    description=f"User {action}",
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
    
    @staticmethod
    def _get_client_ip(request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware:
    """Simple rate limiting middleware for login attempts"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
    def __call__(self, request):
        # Only apply to login POST requests
        if request.path == '/login/' and request.method == 'POST':
            ip = self._get_client_ip(request)
            cache_key = f"login_attempts_{ip}"
            
            attempts = cache.get(cache_key, 0)
            
            if attempts >= self.max_attempts:
                messages.error(request, 'Too many login attempts. Please try again in 5 minutes.')
                return redirect('login')
            
            # Increment attempts
            cache.set(cache_key, attempts + 1, self.lockout_duration)
        
        response = self.get_response(request)
        
        # Clear attempts on successful login
        if request.path == '/login/' and response.status_code == 302 and request.user.is_authenticated:
            ip = self._get_client_ip(request)
            cache.delete(f"login_attempts_{ip}")
        
        return response
    
    @staticmethod
    def _get_client_ip(request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip