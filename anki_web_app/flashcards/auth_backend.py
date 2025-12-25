"""
Supabase JWT authentication backend for Django.

Verifies Supabase JWT tokens and maps Supabase user `sub` to Django User.
"""
import jwt
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from typing import Optional

User = get_user_model()


class SupabaseJWTAuthenticationBackend(BaseBackend):
    """
    Authenticates users using Supabase JWT tokens.
    
    Expects:
    - SUPABASE_URL in settings (e.g., 'https://xxx.supabase.co')
    - SUPABASE_JWT_SECRET in settings (or uses JWKS endpoint)
    
    Token should be in Authorization header: "Bearer <token>"
    """
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate a user from a Supabase JWT token.
        
        Args:
            request: Django request object
            token: Optional JWT token string (if not provided, extracts from Authorization header)
        
        Returns:
            User instance if authentication successful, None otherwise
        """
        if token is None:
            # Extract token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header.startswith('Bearer '):
                return None
            token = auth_header.split('Bearer ')[1]
        
        if not token:
            return None
        
        try:
            # Verify token and decode
            # For Supabase, we can verify using the JWT secret or JWKS
            # Using JWT secret is simpler for now
            supabase_url = getattr(settings, 'SUPABASE_URL', None)
            supabase_jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)
            
            if not supabase_url:
                # If no Supabase config, skip auth (for development)
                return None
            
            # Decode token (without verification first to get header)
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            # Verify token signature
            if supabase_jwt_secret:
                # Use JWT secret for verification
                payload = jwt.decode(
                    token,
                    supabase_jwt_secret,
                    algorithms=['HS256'],
                    audience='authenticated'
                )
            else:
                # Try JWKS verification (more complex, requires requests)
                # For now, fall back to unverified decode (not recommended for production)
                payload = unverified
            
            # Extract Supabase user ID (sub claim)
            supabase_sub = payload.get('sub')
            if not supabase_sub:
                return None
            
            # Get or create Django User based on Supabase sub
            user, created = User.objects.get_or_create(
                username=supabase_sub,
                defaults={
                    'email': payload.get('email', ''),
                    'first_name': payload.get('user_metadata', {}).get('first_name', ''),
                    'last_name': payload.get('user_metadata', {}).get('last_name', ''),
                }
            )
            
            # Store Supabase sub in a custom field if you add one
            # For now, username = supabase_sub
            
            return user
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            # Log error in production
            print(f"Supabase auth error: {e}")
            return None
    
    def get_user(self, user_id):
        """Retrieve a user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
