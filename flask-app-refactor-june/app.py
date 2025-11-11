from flask import Flask, render_template, request, redirect, url_for
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import os

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Initialize CORS for API endpoints
    # SECURITY: Always set CORS_ORIGINS environment variable in production
    # Never use '*' wildcard in production as it allows any origin
    cors_origins_env = os.environ.get('CORS_ORIGINS', '')

    # Parse CORS origins, handling both development and production
    if cors_origins_env:
        cors_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
    else:
        # Development only: allow localhost
        if app.config.get('DEBUG'):
            cors_origins = ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:5000']
        else:
            # Production: Require explicit configuration
            cors_origins = []
            app.logger.warning('CORS_ORIGINS not configured. API endpoints will reject cross-origin requests.')

    if cors_origins:
        CORS(app, resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "allow_headers": ["Content-Type", "X-API-Key"],
                "expose_headers": ["Content-Type"],
                "supports_credentials": False,
                "allow_private_network": False,  # Security: Explicitly deny private network access
                "max_age": 3600
            }
        })

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URI', 'memory://'),
        strategy="fixed-window"
    )
    # Store limiter in app config so routes can access it
    app.limiter = limiter

    # Initialize extensions with app
    from models import db
    db.init_app(app)

    migrate = Migrate()
    migrate.init_app(app, db)

    # Initialize security logger
    from utils.security_logger import security_logger
    security_logger.init_app(app)
    app.security_logger = security_logger

    # Initialize email service
    from utils.email_service import email_service
    email_service.init_app(app)
    app.email_service = email_service
    
    # Import models (needed for migrations)
    from models import User, BlogDraft, DraftVersion
    
    # Security middleware
    @app.before_request
    def force_https():
        """Force HTTPS in production"""
        if app.config.get('FORCE_HTTPS'):
            if not request.is_secure and not app.debug:
                return redirect(request.url.replace('http://', 'https://'))
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        # HTTPS Strict Transport Security
        if app.config.get('FORCE_HTTPS'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy - restrict access to browser features
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=(self), "
            "vibrate=(), "
            "fullscreen=(self), "
            "sync-xhr=()"
        )
        response.headers['Permissions-Policy'] = permissions_policy

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
        )

        # Add upgrade-insecure-requests in production
        if app.config.get('FORCE_HTTPS'):
            csp += "upgrade-insecure-requests;"

        response.headers['Content-Security-Policy'] = csp

        return response
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.drafts import drafts_bp
    from routes.api import api_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(drafts_bp, url_prefix='/drafts')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # CSRF error handler
    @app.errorhandler(400)
    def csrf_error(error):
        if error.description == "The CSRF token is missing.":
            return render_template('errors/csrf_error.html'), 400
        return render_template('500.html'), 400

    # Rate limit error handler
    @app.errorhandler(429)
    def ratelimit_error(error):
        from flask import jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        return render_template('500.html'), 429
    
    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'datetime': datetime
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from models import db
        db.create_all()
    
    # Development server settings
    if app.config.get('DEBUG'):
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        # Production should use a proper WSGI server
        app.run(debug=False, host='0.0.0.0', port=8000)