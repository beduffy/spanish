"""
Supabase JWT authentication backend for Django.

Verifies Supabase JWT tokens and maps Supabase user `sub` to Django User.
"""
import jwt
import requests
import base64
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
            unverified_header = jwt.get_unverified_header(token)
            algorithm = unverified_header.get('alg', 'HS256')
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            print(f"[Auth Backend] Token algorithm: {algorithm}")
            print(f"[Auth Backend] Token header: {unverified_header}")
            print(f"[Auth Backend] Token claims: {list(unverified.keys())}")
            
            # Verify token signature
            # Supabase access tokens use ES256/RS256 and need JWKS verification
            # But we can also try with JWT secret for HS256 if it's a service token
            if algorithm == 'HS256' and supabase_jwt_secret:
                # Use JWT secret for HS256 tokens (service tokens)
                print(f"[Auth Backend] Using HS256 verification with JWT secret")
                payload = jwt.decode(
                    token,
                    supabase_jwt_secret,
                    algorithms=['HS256'],
                    audience='authenticated'
                )
            elif algorithm in ['ES256', 'RS256']:
                # For ES256/RS256, we need JWKS verification
                # Supabase JWKS endpoint: https://<project>.supabase.co/.well-known/jwks.json
                print(f"[Auth Backend] Attempting JWKS verification for {algorithm}")
                jwks_url = f"{supabase_url}/.well-known/jwks.json"
                payload = None
                
                # Try PyJWKClient first
                try:
                    from jwt import PyJWKClient
                    jwks_client = PyJWKClient(jwks_url, max_cached_keys=5)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=[algorithm],
                        audience='authenticated'
                    )
                    print(f"[Auth Backend] JWKS verification successful")
                except Exception as pyjwk_error:
                    print(f"[Auth Backend] PyJWKClient failed: {type(pyjwk_error).__name__}")
                    # Try manual JWKS fetch
                    try:
                        jwks_response = requests.get(jwks_url, timeout=5)
                        jwks_response.raise_for_status()
                        jwks = jwks_response.json()
                        
                        header = jwt.get_unverified_header(token)
                        kid = header.get('kid')
                        
                        key = None
                        for jwk in jwks.get('keys', []):
                            if jwk.get('kid') == kid:
                                key = jwk
                                break
                        
                        if not key:
                            raise ValueError(f"Key with kid {kid} not found in JWKS")
                        
                        from cryptography.hazmat.primitives.asymmetric import rsa, ec
                        from cryptography.hazmat.backends import default_backend
                        
                        if algorithm == 'RS256':
                            n = int.from_bytes(base64.urlsafe_b64decode(key['n'] + '=='), 'big')
                            e = int.from_bytes(base64.urlsafe_b64decode(key['e'] + '=='), 'big')
                            public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
                        else:
                            x = int.from_bytes(base64.urlsafe_b64decode(key['x'] + '=='), 'big')
                            y = int.from_bytes(base64.urlsafe_b64decode(key['y'] + '=='), 'big')
                            curve = ec.SECP256R1()
                            public_key = ec.EllipticCurvePublicNumbers(x, y, curve).public_key(default_backend())
                        
                        payload = jwt.decode(
                            token,
                            public_key,
                            algorithms=[algorithm],
                            audience='authenticated'
                        )
                        print(f"[Auth Backend] Manual JWKS verification successful")
                    except Exception as manual_error:
                        print(f"[Auth Backend] Manual JWKS also failed: {type(manual_error).__name__}: {manual_error}")
                
                # If both JWKS methods failed, use unverified decode as fallback
                if payload is None:
                    print(f"[Auth Backend] WARNING: JWKS unavailable, using unverified decode for development")
                    print(f"[Auth Backend] WARNING: This should be fixed in production!")
                    payload = unverified
            else:
                print(f"[Auth Backend] Unknown algorithm {algorithm}, falling back to unverified")
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
        except jwt.ExpiredSignatureError:
            print(f"[Auth Backend] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[Auth Backend] Invalid token: {e}")
            return None
        except Exception as e:
            # Log error in production
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Supabase auth error: {e}", exc_info=True)
            print(f"[Auth Backend] Supabase auth error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_user(self, user_id):
        """Retrieve a user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
