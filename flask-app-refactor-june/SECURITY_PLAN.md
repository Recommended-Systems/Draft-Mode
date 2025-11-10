# Security Plan for SaaS Deployment

**Status:** Draft Mode - Pre-Production Security Assessment
**Last Updated:** 2025-11-09
**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## Executive Summary

This document outlines security vulnerabilities and remediation steps required before deploying Draft Mode as a SaaS solution for unknown users. The application has a solid foundation with CSRF protection, HTTPS enforcement, and secure session cookies configured, but several critical gaps must be addressed.

---

## 🔴 CRITICAL PRIORITY

### 1. Missing Flask-WTF Dependency
**Issue:** `config.py` enables CSRF protection via Flask-WTF, but the package is missing from `requirements.txt`.

**Impact:** Application will crash in production when CSRF protection is enabled.

**Remediation:**
```bash
# Add to requirements.txt
Flask-WTF==1.2.1
```

**Files to Update:**
- `requirements.txt`

**Verification:** Test all POST endpoints with CSRF tokens in production mode.

---

### 2. Weak Password Policy
**Issue:** Minimum password length is only 6 characters (`routes/auth.py:21`, `routes/settings.py:41`).

**Impact:** Vulnerable to brute force attacks and dictionary attacks.

**Remediation:**
- Increase minimum to 12 characters
- Require complexity (uppercase, lowercase, numbers, special chars)
- Implement password strength meter on frontend
- Add common password blacklist (e.g., `rockyou.txt` common passwords)

**Implementation:**
```python
# Create utils/password_validator.py
import re

def validate_password_strength(password):
    """Validate password meets security requirements"""
    errors = []

    if len(password) < 12:
        errors.append("Password must be at least 12 characters long")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain lowercase letters")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain uppercase letters")

    if not re.search(r"\d", password):
        errors.append("Password must contain numbers")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain special characters")

    # Check against common passwords
    if is_common_password(password):
        errors.append("Password is too common, please choose a stronger one")

    return len(errors) == 0, errors
```

**Files to Update:**
- `routes/auth.py` (signup function)
- `routes/settings.py` (profile function)

---

### 3. No Rate Limiting
**Issue:** No protection against brute force attacks on authentication endpoints.

**Impact:** Attackers can perform unlimited login/signup attempts, credential stuffing, API abuse.

**Remediation:**
Install and configure Flask-Limiter:

```bash
# Add to requirements.txt
Flask-Limiter==3.5.0
```

```python
# In app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"  # Use Redis in production
)

# In routes/auth.py
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    ...

@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("3 per hour")
def signup():
    ...
```

**Recommended Limits:**
- Login: 5 attempts per minute per IP
- Signup: 3 per hour per IP
- API endpoints: 100 requests per hour per user
- Draft save: 60 per minute per user
- Share link generation: 10 per hour per user

**Files to Update:**
- `app.py`
- `routes/auth.py`
- `routes/drafts.py`
- `routes/api.py`

---

### 4. SQL Injection Vulnerabilities
**Issue:** Direct SQL usage in event listeners (`models.py:210-226`) with text() and parameter binding.

**Impact:** While parameterized, the pattern is risky and could be exploited if modified incorrectly.

**Current Code (models.py:210-218):**
```python
version_count = connection.execute(
    db.text("SELECT COUNT(*) FROM draft_versions WHERE blog_draft_id = :draft_id"),
    {"draft_id": target.blog_draft_id}
).scalar()
```

**Status:** Currently safe due to parameterization, but needs review.

**Remediation:**
- Prefer ORM methods over raw SQL
- Add SQLAlchemy query logging in development
- Implement query review process before deployment
- Consider using SQLAlchemy Core expressions instead of text()

**Files to Review:**
- `models.py` (lines 204-226)
- All `query.filter_by()` and `query.filter()` calls

---

### 5. Missing Database Configuration for Production
**Issue:** Using SQLite in production (`config.py:46`), no connection pooling, no backup strategy.

**Impact:**
- SQLite doesn't handle concurrent writes well
- No ACID guarantees under load
- Single point of failure
- No replication/backup

**Remediation:**
```python
# config.py - ProductionConfig
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # PostgreSQL
if not SQLALCHEMY_DATABASE_URI:
    raise ValueError("DATABASE_URL must be set for production")

# PostgreSQL settings
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20
}
```

**Action Items:**
- Migrate to PostgreSQL or MySQL
- Set up automated backups (daily + point-in-time recovery)
- Configure read replicas for scaling
- Implement database connection pooling

---

### 6. XSS Vulnerability in Markdown Rendering
**Issue:** User content is rendered with `Markup()` in `routes/main.py:43` without sanitization.

**Impact:** Malicious users can inject JavaScript into shared drafts.

**Current Code (routes/main.py:31-43):**
```python
html_content = markdown.markdown(
    version.content,
    extensions=['extra', 'codehilite', 'fenced_code']
)

return render_template('public_view.html',
                     html_content=Markup(html_content))
```

**Remediation:**
Install and use Bleach for HTML sanitization:

```bash
# Add to requirements.txt
bleach==6.1.0
```

```python
import bleach

# Allowed HTML tags and attributes
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'ul', 'ol', 'li', 'a', 'img'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title'],
    'code': ['class']
}

html_content = markdown.markdown(
    version.content,
    extensions=['extra', 'codehilite', 'fenced_code']
)

# Sanitize the HTML
safe_html = bleach.clean(
    html_content,
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    strip=True
)

return render_template('public_view.html',
                     html_content=Markup(safe_html))
```

**Files to Update:**
- `routes/main.py`
- `routes/drafts.py` (preview functions)

---

## 🟠 HIGH PRIORITY

### 7. No Email Verification
**Issue:** Users can sign up with any email address without verification.

**Impact:**
- Fake accounts
- Email address harvesting
- Spam/abuse
- No account recovery mechanism

**Remediation:**
Implement email verification workflow:

1. Generate verification token on signup
2. Send verification email
3. Require verification before full access
4. Add `email_verified` and `verification_token` to User model

```python
# models.py additions
class User(db.Model):
    # ... existing fields ...
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)

    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
```

**Required Services:**
- Email service (SendGrid, AWS SES, Mailgun)
- Email templates
- Verification route handler

**Files to Create/Update:**
- `models.py`
- `routes/auth.py`
- `utils/email.py` (new)
- Email templates

---

### 8. No Password Reset Functionality
**Issue:** Users cannot reset forgotten passwords.

**Impact:** Users permanently locked out of accounts, poor user experience.

**Remediation:**
Implement secure password reset:

```python
# models.py additions
class User(db.Model):
    # ... existing fields ...
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)

    def verify_reset_token(self, token):
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return True
```

**Implementation Steps:**
1. Add "Forgot Password" link on login page
2. Send reset email with time-limited token
3. Create reset password form
4. Invalidate token after use
5. Notify user via email when password changes

**Files to Create/Update:**
- `routes/auth.py`
- `utils/email.py`
- Templates for forgot password flow

---

### 9. User Enumeration Vulnerability
**Issue:** Different error messages reveal if email exists (`routes/auth.py:26-27`, `auth.py:65-76`).

**Current Code:**
```python
# Signup
if User.query.filter_by(email=email).first():
    flash('Email already registered')  # ❌ Reveals email exists

# Login
if user and user.check_password(password):
    # success
else:
    flash('Invalid email or password')  # ✅ Generic message
```

**Impact:** Attackers can enumerate valid user accounts.

**Remediation:**
```python
# Signup - route/auth.py
if User.query.filter_by(email=email).first():
    # Don't reveal email exists, log silently
    logger.warning(f"Signup attempt with existing email from {request.remote_addr}")
    # Still show success message and send email to existing account warning them
    flash('If this email is not already registered, check your inbox for verification')
    return redirect(url_for('auth.login'))
```

**Files to Update:**
- `routes/auth.py`

---

### 10. No Logging and Monitoring
**Issue:** No audit trail for security events, making incident response impossible.

**Impact:** Cannot detect breaches, track abuse, or debug issues.

**Remediation:**
Implement comprehensive logging:

```python
# utils/security_logger.py
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class SecurityLogger:
    def __init__(self, app):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

        # File handler
        handler = RotatingFileHandler(
            'logs/security.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_event(self, event_type, user_id=None, ip_address=None, details=None):
        """Log security event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details
        }
        self.logger.info(json.dumps(event))

# Events to log:
# - Login attempts (success/failure)
# - Signup attempts
# - Password changes
# - Account deletions
# - Failed CSRF validations
# - Rate limit violations
# - Share link generation
# - API access
```

**Files to Create:**
- `utils/security_logger.py`
- Update all routes to log security events

---

### 11. Account Lockout Missing
**Issue:** No account lockout after failed login attempts.

**Impact:** Unlimited brute force attempts even with rate limiting (rate limits can be bypassed).

**Remediation:**
```python
# models.py additions
class User(db.Model):
    # ... existing fields ...
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    def is_locked(self):
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def record_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock for 30 minutes
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

# routes/auth.py - login function
def login():
    # ... existing code ...
    user = User.query.filter_by(email=email).first()

    if user and user.is_locked():
        flash('Account temporarily locked due to multiple failed attempts')
        return render_template('login.html')

    if user and user.check_password(password):
        user.reset_failed_attempts()
        # ... proceed with login ...
    else:
        if user:
            user.record_failed_login()
        flash('Invalid email or password')
```

**Files to Update:**
- `models.py`
- `routes/auth.py`

---

### 12. Content Size Limits Missing
**Issue:** No limits on draft content size, database fields, or version counts.

**Impact:**
- DoS via large content
- Database bloat
- Performance degradation

**Remediation:**
```python
# config.py
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
DRAFT_CONTENT_MAX_SIZE = 1 * 1024 * 1024  # 1MB per draft
MAX_VERSIONS_PER_DRAFT = 50
MAX_DRAFTS_PER_USER = 100

# routes/drafts.py - validation
def save_version(version_id):
    content = request.json.get('content', '')

    # Validate content size
    if len(content.encode('utf-8')) > current_app.config['DRAFT_CONTENT_MAX_SIZE']:
        return jsonify({
            'success': False,
            'error': 'Content exceeds maximum size of 1MB'
        }), 413

    # Check version count
    version_count = DraftVersion.query.filter_by(
        blog_draft_id=version.blog_draft_id
    ).count()

    if version_count >= current_app.config['MAX_VERSIONS_PER_DRAFT']:
        return jsonify({
            'success': False,
            'error': 'Maximum versions per draft exceeded'
        }), 403
```

**Files to Update:**
- `config.py`
- `routes/drafts.py`
- Frontend to show character count warnings

---

## 🟡 MEDIUM PRIORITY

### 13. Session Fixation Vulnerability
**Issue:** No session regeneration after login/logout (`routes/auth.py`).

**Impact:** Session fixation attacks possible.

**Remediation:**
```python
from flask import session

# routes/auth.py - login function
if user and user.check_password(password):
    # Regenerate session to prevent fixation
    session.clear()
    session['user_id'] = user.id
    session.permanent = True
    session.modified = True
```

**Files to Update:**
- `routes/auth.py` (login, logout, signup)

---

### 14. No CORS Configuration
**Issue:** No CORS headers configured if API needs to be accessed from other domains.

**Impact:** Cannot build separate frontend or mobile apps.

**Remediation:**
```bash
# Add to requirements.txt
Flask-CORS==4.0.0
```

```python
# app.py
from flask_cors import CORS

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "X-CSRFToken"]
    }
})
```

---

### 15. Share Token Expiration Missing
**Issue:** Share tokens (`models.py:131`) never expire.

**Impact:** Shared links remain valid forever, even if user wants to revoke.

**Remediation:**
```python
# models.py
class DraftVersion(db.Model):
    # ... existing fields ...
    share_token_expires = db.Column(db.DateTime, nullable=True)

    def generate_share_token(self, expires_in_days=30):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
            self.share_token_expires = datetime.utcnow() + timedelta(days=expires_in_days)

    def is_share_token_valid(self):
        if not self.share_token_expires:
            return True  # Tokens created before expiration feature
        return datetime.utcnow() < self.share_token_expires

# routes/main.py
def public_view(share_token):
    version = DraftVersion.query.filter_by(share_token=share_token).first_or_404()

    if not version.is_share_token_valid():
        abort(410)  # Gone
```

**Files to Update:**
- `models.py`
- `routes/main.py`

---

### 16. Missing Security Headers
**Issue:** Some security headers present but could be improved (`app.py:42-70`).

**Current Implementation:** Good foundation exists.

**Enhancements:**
```python
# app.py - add_security_headers function
response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

# Update CSP to be stricter
csp = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com; "  # Use nonces instead of unsafe-inline
    "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)
```

---

### 17. No API Authentication for JSON Endpoints
**Issue:** API endpoints only check `@login_required` but no API key/token mechanism.

**Impact:** Cannot build mobile apps or third-party integrations securely.

**Remediation:**
Implement API token authentication for `/api/*` endpoints:

```python
# models.py
class User(db.Model):
    # ... existing fields ...
    api_token = db.Column(db.String(64), unique=True, nullable=True)
    api_token_created = db.Column(db.DateTime, nullable=True)

    def generate_api_token(self):
        self.api_token = secrets.token_urlsafe(48)
        self.api_token_created = datetime.utcnow()

# utils/decorators.py
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        user = User.query.filter_by(api_token=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Make user available to route
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
```

---

### 18. No Input Validation
**Issue:** Limited validation on user inputs (names, titles, descriptions).

**Impact:**
- Special characters could cause issues
- Unicode issues
- Database encoding problems

**Remediation:**
Create input validator utility:

```python
# utils/validators.py
import re
from bleach import clean

def sanitize_text_input(text, max_length=None):
    """Sanitize text input"""
    if not text:
        return ''

    # Strip whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace('\x00', '')

    # Limit length
    if max_length:
        text = text[:max_length]

    return text

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_html_input(text):
    """Remove all HTML tags from input"""
    return clean(text, tags=[], strip=True)
```

Apply to all form inputs.

---

## 🟢 LOW PRIORITY / ENHANCEMENTS

### 19. Two-Factor Authentication (2FA)
**Recommendation:** Add optional 2FA for enhanced security.

**Implementation:** Use PyOTP for TOTP-based 2FA.

---

### 20. Security Audit Trail
**Recommendation:** Detailed audit log of all user actions.

**Use Cases:**
- Compliance (GDPR, SOC2)
- Incident response
- User support

---

### 21. Dependency Security Scanning
**Recommendation:**
```bash
# Add to CI/CD pipeline
pip install safety
safety check --json

# Or use GitHub Dependabot
```

---

### 22. GDPR Compliance
**Requirements:**
- Privacy policy
- Cookie consent
- Data export functionality
- Right to be forgotten (already implemented via account deletion)
- Data processing agreement

---

### 23. Database Encryption at Rest
**Recommendation:** Use database-level encryption for sensitive data.

**Options:**
- PostgreSQL: pgcrypto extension
- MySQL: Transparent Data Encryption (TDE)
- Application-level: SQLAlchemy-Utils encrypted columns

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] Add Flask-WTF to requirements.txt
- [ ] Implement rate limiting
- [ ] Strengthen password requirements
- [ ] Fix XSS vulnerability in markdown rendering
- [ ] Migrate to PostgreSQL
- [ ] Add content size limits

### Phase 2: High Priority (Week 2-3)
- [ ] Email verification system
- [ ] Password reset functionality
- [ ] Implement logging and monitoring
- [ ] Account lockout mechanism
- [ ] Fix user enumeration
- [ ] Session fixation protection

### Phase 3: Medium Priority (Week 4)
- [ ] Share token expiration
- [ ] Enhanced security headers
- [ ] API token authentication
- [ ] Input validation across all forms
- [ ] CORS configuration

### Phase 4: Long-term Enhancements
- [ ] Two-factor authentication
- [ ] Security audit trail
- [ ] GDPR compliance features
- [ ] Database encryption

---

## Testing Checklist

Before production deployment:

### Security Testing
- [ ] Run OWASP ZAP or Burp Suite security scan
- [ ] Test SQL injection on all database queries
- [ ] Test XSS on all user input fields
- [ ] Test CSRF protection on all POST endpoints
- [ ] Test authentication bypass attempts
- [ ] Test rate limiting effectiveness
- [ ] Test password reset token security
- [ ] Test share token security
- [ ] Test file upload vulnerabilities (if applicable)

### Penetration Testing
- [ ] Conduct internal penetration test
- [ ] Consider external security audit
- [ ] Test for privilege escalation
- [ ] Test for information disclosure

### Code Review
- [ ] Review all database queries
- [ ] Review all user input handling
- [ ] Review authentication/authorization logic
- [ ] Review session management
- [ ] Review error handling (no information leakage)

---

## Monitoring and Incident Response

### Monitoring Setup
```python
# Use Sentry or similar for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Alerts to Configure
- Failed login attempts > 100/hour
- New user signups > 50/hour
- Database errors
- Rate limit violations
- CSRF validation failures
- 500 errors
- Unusual API usage patterns

### Incident Response Plan
1. Detect: Monitoring alerts trigger
2. Assess: Review logs and determine severity
3. Contain: Disable affected accounts/features
4. Investigate: Root cause analysis
5. Remediate: Apply fixes
6. Document: Post-mortem report
7. Prevent: Update security measures

---

## Production Deployment Checklist

### Environment Configuration
- [ ] Set strong SECRET_KEY (256-bit random)
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for rate limiting and caching
- [ ] Configure email service (SendGrid/SES)
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup system
- [ ] Set up monitoring (Sentry, DataDog, etc.)

### Security Configuration
- [ ] DEBUG = False
- [ ] FORCE_HTTPS = True
- [ ] WTF_CSRF_ENABLED = True
- [ ] SESSION_COOKIE_SECURE = True
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Security headers enabled

### Infrastructure
- [ ] Use WSGI server (Gunicorn/uWSGI)
- [ ] Place behind reverse proxy (Nginx)
- [ ] Configure firewall rules
- [ ] Set up load balancing (if needed)
- [ ] Configure auto-scaling
- [ ] Set up CDN for static assets

---

## Compliance Considerations

### Data Privacy
- Users can delete their accounts (implemented)
- Need to add data export functionality
- Add privacy policy and terms of service
- Cookie consent banner

### Data Retention
- Define retention policy for deleted accounts
- Implement automated cleanup of old data
- Keep audit logs for required period

### Geographic Considerations
- GDPR (Europe): Right to access, right to be forgotten
- CCPA (California): Similar requirements
- Consider data residency requirements

---

## Cost Estimates for Implementation

### Services Required
- **PostgreSQL Database:** $15-50/month (managed)
- **Redis:** $10-30/month (managed)
- **Email Service:** $0-10/month (first 10k emails free)
- **Monitoring/Logging:** $0-50/month (Sentry free tier available)
- **SSL Certificates:** $0 (Let's Encrypt)
- **Backup Storage:** $5-20/month

**Total Estimated Monthly Cost:** $30-160/month depending on scale

### Development Time
- Phase 1 (Critical): 40-60 hours
- Phase 2 (High): 60-80 hours
- Phase 3 (Medium): 40-60 hours
- Testing & QA: 40 hours

**Total: 180-240 hours (~6-8 weeks for 1 developer)**

---

## Resources

### Security Best Practices
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/en/latest/security/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html

### Tools
- Safety (dependency scanning): https://pyup.io/safety/
- Bandit (static analysis): https://bandit.readthedocs.io/
- OWASP ZAP: https://www.zaproxy.org/

---

## Sign-off

Before deploying to production with real users, all **Critical** and **High** priority items must be addressed. **Medium** priority items should be addressed within 30 days of launch. **Low** priority items can be planned for future releases.

**Security Contact:** [Add security team contact]
**Next Review Date:** [Set quarterly review]
