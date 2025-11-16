# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Draft Mode is a retro-styled blog draft management system built with Flask. It provides version control for blog posts, allowing users to create multiple versions of their drafts, compare them, and share them via public links.

## Development Commands

### Setup and Environment

**Important**: This system is configured to use `python` (not `python3`) for the virtual environment and running the application.

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Database Management
```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade

# View migration history
flask db history

# View current migration
flask db current

# Reset database (WARNING: deletes all data)
rm draft_mode_dev.db
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Running the Application
```bash
# Development server (recommended)
python app.py

# Alternative using Flask CLI
flask run

# Run on custom port
flask run --port 5001

# Production (use proper WSGI server instead)
gunicorn app:app
```

### Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///draft_mode_dev.db
FLASK_ENV=development
FLASK_APP=app.py
```

## Architecture Overview

### Application Factory Pattern
The application uses the factory pattern (`create_app()` in `app.py`) with three config modes:
- **DevelopmentConfig**: SQLite database, CSRF disabled, HTTP allowed
- **ProductionConfig**: Requires SECRET_KEY, enforces HTTPS, CSRF enabled
- **TestingConfig**: In-memory SQLite, security features disabled for testing

Configuration is loaded from `config.py` based on the environment.

### Database Models (models.py)

**User Model**
- Handles authentication with password hashing (Werkzeug)
- Account lockout after 5 failed login attempts (30-minute lock)
- Email verification with tokens (24-hour expiry)
- Password reset tokens (1-hour expiry)
- API token generation for programmatic access
- Relationships: One-to-many with BlogDraft (cascade delete)

**BlogDraft Model**
- Container for multiple versions of a draft
- Properties: `current_version`, `latest_version`, `has_final_version`, `status`
- Status derived from versions: 'empty', 'final', or 'active'
- Relationships: One-to-many with DraftVersion (cascade delete)

**DraftVersion Model**
- Individual version of a blog post with markdown content
- Tags: 'draft', 'final', 'ready_for_review', 'working'
- Share tokens for public access (30-day default expiry)
- Properties: `word_count`, `character_count`, `is_final`, `display_name`
- `set_as_current()` method marks version as active
- `set_tag()` ensures tag uniqueness for special tags

**SQLAlchemy Event Listeners**
- `after_insert` on DraftVersion: Automatically sets first version as current
- `after_update` on DraftVersion: Updates parent BlogDraft's `updated_at` timestamp

### Blueprint Architecture (routes/)

**auth.py** (`/auth` prefix)
- Session-based authentication with Flask sessions
- Login: Validates credentials, handles account lockout, logs security events
- Signup: Sanitizes input, validates password strength, creates user
- Password reset: Token-based reset flow with email notifications
- Email verification: Token-based verification (not required for login)
- Security: Session regeneration on login/logout to prevent fixation

**drafts.py** (`/drafts` prefix)
- Draft CRUD operations with ownership verification
- Version management: create, save, delete, duplicate, rename
- Tagging system: mark versions as draft/final/review/working
- Share link generation with expiring tokens
- Content size limits enforced (1MB per draft by default)
- Version limits enforced (50 versions per draft by default)
- Markdown preview with XSS protection via `render_markdown_safe()`

**api.py** (`/api` prefix)
- RESTful JSON API for draft and user statistics
- Endpoints: `/drafts`, `/drafts/<id>/stats`, `/drafts/<id>/versions`, `/user/stats`
- Protected with `@login_required` decorator
- Returns JSON with ISO 8601 timestamps

**main.py** (no prefix)
- Public pages: index, dashboard, public view (share links)
- Dashboard: Lists all user drafts with stats
- Public view: Renders shared draft versions (token validation)

**settings.py** (`/settings` prefix)
- User account management
- API token generation/revocation
- Password changes with strength validation

### Security Features

**Authentication & Session Management**
- Session cookies: Secure (HTTPS-only in prod), HttpOnly, SameSite=Lax
- Session regeneration on login/signup/logout prevents fixation attacks
- Account lockout: 5 failed attempts = 30-minute lock
- Password strength validation in `utils/password_validator.py`

**Input Validation & Sanitization**
- All user inputs sanitized via `utils/input_validator.py`
- Email, name, draft title, version name validation with regex
- HTML stripping with bleach library
- Control character removal (except newlines/tabs)
- Null byte removal to prevent injection attacks

**XSS Protection**
- Markdown rendering via `utils/markdown_renderer.py`
- Bleach library sanitizes HTML output
- Allowed tags/attributes whitelist
- URL protocols restricted to http/https/mailto
- Code syntax highlighting with Pygments (safe)

**CSRF Protection**
- Flask-WTF CSRF protection enabled in production
- 1-hour token lifetime
- Disabled in development/testing for convenience

**Security Headers** (added in `app.py`)
- Strict-Transport-Security (HSTS): 1 year with preload
- X-Frame-Options: DENY (clickjacking protection)
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Restricts browser features (camera, microphone, etc.)
- Content-Security-Policy: Restricts script/style/img sources
  - Scripts: self, unsafe-inline, cdnjs.cloudflare.com
  - Styles: self, unsafe-inline, fonts.googleapis.com
  - Fonts: self, fonts.gstatic.com
  - Images: self, data URIs

**Rate Limiting**
- Flask-Limiter: 200 requests/day, 50 requests/hour per IP
- Uses memory storage in development (switch to Redis in production)
- Rate limit storage URI: `RATELIMIT_STORAGE_URI` config
- Custom rate limits can be set per route

**CORS Configuration**
- Enabled for `/api/*` endpoints only
- Development: localhost:3000, localhost:5000, 127.0.0.1:5000
- Production: Requires explicit `CORS_ORIGINS` environment variable
- Never use wildcard `*` in production
- Methods: GET, POST, PUT, DELETE
- Headers: Content-Type, X-API-Key
- Credentials: False (no cookies cross-origin)

**Content Limits**
- Max request size: 16MB (global)
- Max draft content: 1MB per draft (configurable)
- Max versions per draft: 50 (configurable)
- Max drafts per user: 100 (configurable)

**Security Logging**
- Custom security logger in `utils/security_logger.py`
- Logs: login success/failure, signups, suspicious activity
- Initialized in application factory

### Decorators (utils/decorators.py)

- `@login_required`: Redirects to login if not authenticated, stores intended URL
- `@redirect_if_authenticated`: Prevents logged-in users from accessing auth pages
- `@api_key_required`: Validates X-API-Key header for API endpoints
- `get_current_user()`: Returns current user from session or API key (via flask.g)

### Utilities

**utils/markdown_renderer.py**
- `render_markdown_safe()`: Renders markdown with XSS protection
- Extensions: extra, codehilite, fenced_code, tables
- Bleach sanitization with whitelist
- Automatic URL linkification (skips code blocks)

**utils/input_validator.py**
- `sanitize_text_input()`: Strips whitespace, null bytes, control chars
- `sanitize_html_input()`: Removes all HTML tags
- `validate_email()`: Regex-based email validation
- `validate_name()`: Validates user names (letters, spaces, hyphens, apostrophes)
- `validate_draft_title()`: Max 200 characters
- `validate_version_name()`: Max 100 characters
- `sanitize_filename()`: Prevents directory traversal

**utils/password_validator.py**
- Password strength validation (not included in files read, but referenced)
- Returns validation errors as list

**utils/security_logger.py**
- Security event logging for audit trails
- Methods: `log_login_success()`, `log_login_failure()`, `log_signup()`, `log_logout()`

**utils/email_service.py**
- Email notifications (password reset, verification, password changed)
- Initialized in application factory
- Enabled/disabled via `EMAIL_ENABLED` config

### Frontend Structure

**Templates** (`templates/`)
- Base template: `base.html` with shared layout
- Auth: `login.html`, `signup.html`, `forgot_password.html`, `reset_password.html`
- Drafts: `dashboard.html`, `create_draft.html`, `edit_draft.html`, `compare.html`
- Public: `public_view.html` for shared drafts
- Errors: `404.html`, `500.html`

**Static Assets** (`static/`)
- CSS: `base.css`, `editor.css`, `dashboard.css`, `compare.css`, `light-theme.css`
- JavaScript: `editor.js` (main editor functionality), `text-selection-toolbar.js`
- Retro-styled design with focus on editor experience

### Database Migrations

- Managed by Flask-Migrate (Alembic wrapper)
- Migration files in `migrations/versions/`
- Always create migrations for model changes
- Review migration files before applying (check auto-generated code)
- Schema changes should be backward compatible when possible

## Important Development Practices

### Adding New Routes
1. Add route to appropriate blueprint in `routes/`
2. Apply security decorators (`@login_required`, rate limits)
3. Validate and sanitize all inputs using `utils/input_validator.py`
4. Use `get_current_user()` for user identification
5. Return appropriate HTTP status codes
6. Handle exceptions and rollback database sessions

### Modifying Database Models
1. Make changes to `models.py`
2. Create migration: `flask db migrate -m "Description"`
3. Review generated migration in `migrations/versions/`
4. Test migration: `flask db upgrade` and `flask db downgrade`
5. Update model methods if needed
6. Consider data migration if changing existing columns

### Security Considerations
- Always sanitize user input with `sanitize_text_input()` or `sanitize_html_input()`
- Use `render_markdown_safe()` for markdown rendering
- Validate email addresses with `validate_email()`
- Check password strength with `validate_password_strength()`
- Enforce content size limits (use `config.DRAFT_CONTENT_MAX_SIZE`)
- Verify ownership before modifying resources (check `user_id`)
- Log security-relevant events with `security_logger`
- Use parameterized queries (SQLAlchemy ORM handles this)
- Don't reveal user existence in signup/password reset (generic messages)

### Authentication Flow
1. User submits credentials
2. Sanitize email input and convert to lowercase
3. Query user by email
4. Check if account is locked (`user.is_locked()`)
5. Verify password (`user.check_password()`)
6. On success: Reset failed attempts, regenerate session, log event
7. On failure: Record failed attempt, log event, show generic error

### Version Management Patterns
- Creating versions: Unset `is_current` on other versions, set new version as current
- Deleting versions: Check if it's the only version (prevent), set another as current if needed
- Setting tags: Use `version.set_tag()` to ensure tag uniqueness
- Share tokens: Generate with `version.generate_share_token()`, check validity with `version.is_share_token_valid()`

### Error Handling
- Use `try/except` blocks around database operations
- Always rollback session on exception: `db.session.rollback()`
- Flash user-friendly error messages
- Log detailed errors for debugging (use `current_app.logger.error()`)
- Return appropriate status codes (400, 403, 404, 500)

## Production Deployment Checklist

1. Set strong `SECRET_KEY` environment variable
2. Use PostgreSQL or MySQL (not SQLite)
3. Set `FLASK_ENV=production`
4. Configure `CORS_ORIGINS` with explicit domains
5. Use Redis for rate limiting (`RATELIMIT_STORAGE_URI`)
6. Enable email service (`EMAIL_ENABLED=True`)
7. Use Gunicorn or uWSGI (not Flask dev server)
8. Set up reverse proxy (Nginx/Apache)
9. Enable HTTPS and set `FORCE_HTTPS=True`
10. Configure security headers in reverse proxy
11. Set up backup strategy for database
12. Monitor security logs
13. Configure email service (SMTP settings)

## Common Patterns

### Creating a New Feature Route
```python
@blueprint.route('/feature', methods=['GET', 'POST'])
@login_required
def feature():
    user = get_current_user()

    # Validate ownership
    resource = Model.query.filter_by(id=resource_id, user_id=user.id).first_or_404()

    # Sanitize inputs
    input_data = sanitize_text_input(request.form.get('field', ''), max_length=100)

    # Validate
    if not input_data:
        return jsonify({'error': 'Field required'}), 400

    try:
        # Database operations
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error: {e}")
        return jsonify({'error': 'Operation failed'}), 500
```

### Adding a Model Property
```python
@property
def computed_value(self):
    """Calculate derived value"""
    return some_calculation(self.attribute)
```

### Database Event Listener
```python
from sqlalchemy import event

@event.listens_for(Model, 'after_update')
def on_update(mapper, connection, target):
    """React to model updates"""
    # Use raw SQL via connection, not ORM
    connection.execute(...)
```
