"""
Django REST Framework authentication class for Supabase JWT tokens.
"""
from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from django.conf import settings
from .auth_backend import SupabaseJWTAuthenticationBackend

User = get_user_model()


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class that uses Supabase JWT tokens.
    
    Expects Authorization header: "Bearer <token>"
    In DEBUG mode, also accepts requests without tokens (uses middleware-set user or test user).
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        # If user was already set by middleware (DEBUG mode auto-login), use it
        if request.user and request.user.is_authenticated:
            return (request.user, None)
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
            
            if not token:
                return None
            
            # Use our Supabase auth backend
            backend = SupabaseJWTAuthenticationBackend()
            user = backend.authenticate(request, token=token)
            
            if not user:
                raise exceptions.AuthenticationFailed('Invalid or expired token')
            
            return (user, token)
        
        # In DEBUG mode, if no token provided, use test user (for E2E tests)
        if settings.DEBUG and not auth_header:
            test_user, created = User.objects.get_or_create(
                username='testuser',
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                }
            )
            if created:
                test_user.set_unusable_password()
                test_user.save()
            return (test_user, None)
        
        return None
