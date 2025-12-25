"""
Middleware to authenticate requests using Supabase JWT tokens.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()


class SupabaseJWTAuthenticationMiddleware:
    """
    Middleware to authenticate requests using Supabase JWT tokens from Authorization header.
    
    Sets request.user if a valid token is found.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Try to authenticate using Supabase JWT backend
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            from .auth_backend import SupabaseJWTAuthenticationBackend
            backend = SupabaseJWTAuthenticationBackend()
            user = backend.authenticate(request)
            if user:
                request.user = user
        
        response = self.get_response(request)
        return response
