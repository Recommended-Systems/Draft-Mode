import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Session security configuration
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access to session cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Security headers
    FORCE_HTTPS = True
    PREFERRED_URL_SCHEME = 'https'

    # Rate limiting
    RATELIMIT_STORAGE_URI = 'memory://'  # Use Redis in production

    # Content limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    DRAFT_CONTENT_MAX_SIZE = 1 * 1024 * 1024  # 1MB per draft
    MAX_VERSIONS_PER_DRAFT = 50
    MAX_DRAFTS_PER_USER = 100

    # Email configuration
    EMAIL_ENABLED = False  # Set to True in production when configured
    EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@draftmode.app')
    APP_NAME = 'Draft Mode'

    # CORS configuration
    # SECURITY CRITICAL: Set CORS_ORIGINS environment variable in production
    # NEVER use wildcard '*' in production - specify exact origins only
    # Example: CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
    # Leave empty in production to enforce explicit configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///draft_mode_dev.db'
    
    # Development overrides for local testing
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    FORCE_HTTPS = False
    PREFERRED_URL_SCHEME = 'http'
    WTF_CSRF_ENABLED = False  # Disable CSRF in development for easier testing

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # Validate SECRET_KEY at instantiation, not at class definition
    @property
    def SECRET_KEY(self):
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("No SECRET_KEY set for production environment")
        return secret_key

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///draft_mode_prod.db'

    # Production security settings
    SESSION_COOKIE_SECURE = True
    FORCE_HTTPS = True
    PREFERRED_URL_SCHEME = 'https'
    WTF_CSRF_ENABLED = True

    # Rate limiting - use Redis in production
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'redis://localhost:6379')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False