# Security Review & Production Configuration Guide

## Production Environment Configuration

### Current Setup

**Development (`docker-compose.yml`):**
- Uses `.env` file (optional, won't fail if missing)
- Default `SECRET_KEY` for CI/testing
- `DEBUG=True` by default
- Auto-login test user in DEBUG mode

**Production (`docker-compose.prod.yml`):**
- Uses `.env.prod` file (required)
- No default secrets
- `DEBUG=False` (must be set in `.env.prod`)
- No auto-login

### Required Changes for Production

1. **Create `.env.prod` from template:**
   ```bash
   cp env.prod.example .env.prod
   nano .env.prod  # Fill in all values
   ```

2. **Ensure `.env.prod` is NOT committed:**
   - Already in `.gitignore` ✓
   - Verify: `git check-ignore .env.prod`

3. **Key differences in `.env.prod`:**
   - `DEBUG=False` (critical!)
   - `SECRET_KEY` must be strong and unique
   - `ALLOWED_HOSTS` must include your domain
   - `CORS_ALLOWED_ORIGINS` must match your frontend domain
   - All API keys must be set (no defaults)

---

## Security Vulnerabilities Found

### 🔴 CRITICAL Issues

#### 1. **DEBUG Mode Auto-Login in Production Code**
**Location:** `anki_web_app/flashcards/middleware.py:58-74` and `drf_auth.py:58-70`

**Issue:** Code automatically creates/logs in a test user when `DEBUG=True` and no auth token is present.

**Risk:** If `DEBUG` is accidentally set to `True` in production, anyone can access the system without authentication.

**Fix Required:**
```python
# Remove or guard with explicit environment check
if settings.DEBUG and os.environ.get('ALLOW_AUTO_LOGIN') == 'true':
    # Only allow in explicit dev mode
```

#### 2. **JWT Verification Fallback to Unverified Decode**
**Location:** `anki_web_app/flashcards/auth_backend.py:143-147`

**Issue:** If JWKS verification fails, code falls back to unverified token decode.

**Risk:** Tokens could be accepted without proper signature verification in production.

**Fix Required:** Remove fallback, fail authentication if JWKS verification fails.

#### 3. **Missing HTTPS Security Headers**
**Location:** `anki_web_app/spanish_anki_project/settings.py`

**Issue:** No `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`, etc.

**Risk:** Vulnerable to man-in-the-middle attacks, clickjacking, MIME sniffing.

**Fix Required:** Add production security settings (see recommendations below).

#### 4. **No SSL/TLS in Production Nginx**
**Location:** `nginx/production.conf`

**Issue:** Nginx config only listens on HTTP port 80, no HTTPS/SSL.

**Risk:** All traffic is unencrypted, credentials exposed.

**Fix Required:** Add SSL configuration with Let's Encrypt or your SSL certificate.

#### 5. **Default SECRET_KEY in Settings**
**Location:** `anki_web_app/spanish_anki_project/settings.py:38`

**Issue:** Hardcoded default SECRET_KEY that's the same for all installations.

**Risk:** If SECRET_KEY is not set, all installations share the same key, compromising session security.

**Fix Required:** Remove default or make it fail loudly if not set in production.

### 🟡 HIGH Priority Issues

#### 6. **CORS Wildcard with Credentials**
**Location:** `nginx/production.conf:50` and `settings.py:158`

**Issue:** `CORS_ALLOW_CREDENTIALS=True` with `Access-Control-Allow-Origin: *` in nginx.

**Risk:** Browsers will reject this combination, but if misconfigured, could allow credential theft.

**Fix Required:** Set specific origins, not wildcard, when credentials are enabled.

#### 7. **UserScopedMixin Fallback to All Objects**
**Location:** `anki_web_app/flashcards/views.py:42-55`

**Issue:** Falls back to returning all objects if user is anonymous (for "backward compatibility").

**Risk:** If authentication fails silently, users could see other users' data.

**Fix Required:** Remove fallback, require authentication.

#### 8. **Sensitive Data in Print Statements**
**Location:** Multiple files (`middleware.py`, `auth_backend.py`)

**Issue:** Print statements log tokens, user info, auth details.

**Risk:** Logs could expose sensitive data if accessible.

**Fix Required:** Use proper logging with appropriate log levels, remove print statements.

#### 9. **No Rate Limiting**
**Location:** No rate limiting middleware found

**Issue:** API endpoints have no rate limiting protection.

**Risk:** Vulnerable to brute force attacks, DoS, API abuse.

**Fix Required:** Add rate limiting (django-ratelimit or DRF throttling).

#### 10. **File Upload Validation Could Be Stronger**
**Location:** `anki_web_app/flashcards/views.py:464-546`

**Issue:** CSV upload validates file type but doesn't check:
   - File size limits (only nginx has 10M limit)
   - Malicious content
   - Encoding issues
   - Row count limits

**Risk:** DoS via large files, memory exhaustion, malicious CSV parsing.

**Fix Required:** Add Django-level file size validation, row count limits, content validation.

### 🟢 MEDIUM Priority Issues

#### 11. **CSRF Protection May Be Ineffective**
**Location:** `settings.py:65` (CSRF middleware present)

**Issue:** CSRF middleware is present, but with JWT auth and CORS, CSRF tokens may not be properly validated for API endpoints.

**Risk:** CSRF attacks if session-based auth is used.

**Fix Required:** Ensure CSRF is properly configured for your auth method.

#### 12. **SQLite Database Permissions**
**Location:** Database file location and permissions

**Issue:** SQLite file permissions may allow unauthorized access.

**Risk:** Database file could be read/written by other users on the system.

**Fix Required:** Ensure proper file permissions (600) and location outside web root.

#### 13. **No Input Sanitization for User Content**
**Location:** Various views accepting user input

**Issue:** User-provided text (lessons, cards) may contain XSS payloads if rendered unsafely.

**Risk:** XSS attacks if content is rendered in frontend without sanitization.

**Fix Required:** Ensure Vue.js properly escapes content, or sanitize on backend.

---

## Security Recommendations

### Immediate Actions (Before Production)

1. **Fix DEBUG auto-login:**
   - Remove or guard with explicit environment variable
   - Never allow in production

2. **Fix JWT verification:**
   - Remove unverified decode fallback
   - Fail authentication if verification fails

3. **Add HTTPS:**
   - Configure SSL in nginx
   - Use Let's Encrypt for free certificates
   - Redirect HTTP to HTTPS

4. **Add security headers:**
   ```python
   # In settings.py (production only)
   if not DEBUG:
       SECURE_SSL_REDIRECT = True
       SECURE_HSTS_SECONDS = 31536000  # 1 year
       SECURE_HSTS_INCLUDE_SUBDOMAINS = True
       SECURE_HSTS_PRELOAD = True
       SECURE_CONTENT_TYPE_NOSNIFF = True
       SECURE_BROWSER_XSS_FILTER = True
       X_FRAME_OPTIONS = 'DENY'
       SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
   ```

5. **Remove default SECRET_KEY:**
   ```python
   SECRET_KEY = config('SECRET_KEY')
   if not SECRET_KEY and not DEBUG:
       raise ValueError("SECRET_KEY must be set in production!")
   ```

6. **Fix CORS:**
   - Remove wildcard when credentials enabled
   - Set specific origins from environment variable

7. **Add rate limiting:**
   ```python
   # In settings.py
   REST_FRAMEWORK = {
       # ... existing config ...
       'DEFAULT_THROTTLE_CLASSES': [
           'rest_framework.throttling.AnonRateThrottle',
           'rest_framework.throttling.UserRateThrottle'
       ],
       'DEFAULT_THROTTLE_RATES': {
           'anon': '100/hour',
           'user': '1000/hour'
       }
   }
   ```

8. **Remove print statements:**
   - Replace with proper logging
   - Use appropriate log levels
   - Never log tokens or passwords

### Production Checklist

- [ ] `.env.prod` created with all required variables
- [ ] `DEBUG=False` in `.env.prod`
- [ ] Strong `SECRET_KEY` generated (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] `ALLOWED_HOSTS` includes production domain
- [ ] `CORS_ALLOWED_ORIGINS` matches frontend domain
- [ ] SSL/HTTPS configured in nginx
- [ ] Security headers added to settings.py
- [ ] DEBUG auto-login removed/guarded
- [ ] JWT verification fallback removed
- [ ] Rate limiting enabled
- [ ] File upload limits enforced
- [ ] Database file permissions set to 600
- [ ] Logging configured (no print statements)
- [ ] Regular backups configured
- [ ] Monitoring/alerting set up

### Environment Variable Security

**Development:**
- `.env` file (gitignored) ✓
- Can have defaults for local dev
- DEBUG=True acceptable

**Production:**
- `.env.prod` file (gitignored) ✓
- NO defaults - must fail if missing
- DEBUG=False mandatory
- All secrets must be set

**CI/CD:**
- Use GitHub Secrets for sensitive values
- Never commit `.env.prod`
- Use different keys for CI vs production

---

## Additional Security Best Practices

1. **Regular Updates:**
   - Keep Django and dependencies updated
   - Monitor security advisories
   - Update Docker base images

2. **Monitoring:**
   - Set up error tracking (Sentry, etc.)
   - Monitor failed authentication attempts
   - Alert on suspicious activity

3. **Backups:**
   - Regular database backups
   - Test restore procedures
   - Store backups securely

4. **Access Control:**
   - Limit server access (SSH keys only)
   - Use firewall rules
   - Regular security audits

5. **Dependencies:**
   - Regularly audit dependencies (`pip-audit`, `npm audit`)
   - Keep requirements.txt updated
   - Pin versions in production

---

## Summary

**Critical fixes needed before production:**
1. Remove DEBUG auto-login
2. Fix JWT verification fallback
3. Add HTTPS/SSL
4. Add security headers
5. Remove default SECRET_KEY
6. Fix CORS configuration

**High priority:**
7. Add rate limiting
8. Fix UserScopedMixin fallback
9. Remove print statements
10. Strengthen file upload validation

The application has a solid foundation with authentication, user scoping, and proper API structure. The main concerns are production-specific security settings and removing development-only code paths that could be exploited if misconfigured.
