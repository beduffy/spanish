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
        
        # Debug logging (print to stdout for now since logging config might not be set)
        if request.path.startswith('/api/'):
            print(f"[Middleware] Path: {request.path}")
            print(f"[Middleware] Auth header present: {bool(auth_header)}")
            if auth_header:
                print(f"[Middleware] Auth header starts with Bearer: {auth_header.startswith('Bearer ')}")
                if auth_header.startswith('Bearer '):
                    token_preview = auth_header[:50] + '...' if len(auth_header) > 50 else auth_header
                    print(f"[Middleware] Token preview: {token_preview}")
        
        if auth_header.startswith('Bearer '):
            from .auth_backend import SupabaseJWTAuthenticationBackend
            backend = SupabaseJWTAuthenticationBackend()
            try:
                token = auth_header.split('Bearer ')[1]
                print(f"[Middleware] Calling backend.authenticate() with token (first 30 chars): {token[:30]}...")
                user = backend.authenticate(request, token=token)
                if user:
                    request.user = user
                    print(f"[Middleware] Authentication successful for user: {user.username}")
                else:
                    print(f"[Middleware] Authentication FAILED - backend returned None for path: {request.path}")
                    # Check if SUPABASE_URL is configured
                    from django.conf import settings
                    supabase_url = getattr(settings, 'SUPABASE_URL', None)
                    supabase_jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)
                    print(f"[Middleware] SUPABASE_URL configured: {bool(supabase_url)}")
                    print(f"[Middleware] SUPABASE_JWT_SECRET configured: {bool(supabase_jwt_secret)}")
            except Exception as e:
                print(f"[Middleware] Exception during authentication: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[Middleware] No Bearer token found for path: {request.path}")
            # Development-only: Auto-login as test user if DEBUG=True and no token
            from django.conf import settings
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
                    test_user.set_unusable_password()  # Password not needed for JWT auth
                    test_user.save()
                    print(f"[Middleware] Created test user: testuser")
                request.user = test_user
                print(f"[Middleware] Auto-logged in as test user (DEBUG mode)")
        
        response = self.get_response(request)
        return response
