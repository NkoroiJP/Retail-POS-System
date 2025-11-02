from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


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