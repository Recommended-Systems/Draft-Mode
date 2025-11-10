"""Security event logging"""
import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import request, has_request_context


class SecurityLogger:
    """Centralized security event logger"""

    def __init__(self, app=None):
        self.logger = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the logger with the Flask app"""
        # Create logs directory if it doesn't exist
        log_dir = app.config.get('LOG_DIR', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Set up logger
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

        # Rotating file handler (10MB max, keep 10 backups)
        log_file = os.path.join(log_dir, 'security.log')
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )

        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

        # Also log to console in development
        if app.config.get('DEBUG'):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _get_request_info(self):
        """Extract relevant request information"""
        if not has_request_context():
            return {}

        return {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'path': request.path,
            'method': request.method,
            'referrer': request.referrer
        }

    def log_event(self, event_type, user_id=None, details=None, level='info'):
        """
        Log a security event

        Args:
            event_type (str): Type of event (login, logout, failed_login, etc.)
            user_id (int): User ID if applicable
            details (dict): Additional event details
            level (str): Log level (info, warning, error)
        """
        if not self.logger:
            return

        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id
        }

        # Add request context
        event.update(self._get_request_info())

        # Add custom details
        if details:
            event['details'] = details

        # Log as JSON
        log_message = json.dumps(event)

        if level == 'warning':
            self.logger.warning(log_message)
        elif level == 'error':
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)

    # Convenience methods for common events

    def log_login_success(self, user_id, email):
        """Log successful login"""
        self.log_event('login_success', user_id=user_id, details={'email': email})

    def log_login_failure(self, email):
        """Log failed login attempt"""
        self.log_event('login_failure', details={'email': email}, level='warning')

    def log_signup(self, user_id, email):
        """Log new user signup"""
        self.log_event('signup', user_id=user_id, details={'email': email})

    def log_signup_attempt_existing_email(self, email):
        """Log signup attempt with existing email"""
        self.log_event(
            'signup_existing_email',
            details={'email': email},
            level='warning'
        )

    def log_logout(self, user_id):
        """Log user logout"""
        self.log_event('logout', user_id=user_id)

    def log_password_change(self, user_id):
        """Log password change"""
        self.log_event('password_change', user_id=user_id)

    def log_password_change_failure(self, user_id, reason):
        """Log failed password change"""
        self.log_event(
            'password_change_failure',
            user_id=user_id,
            details={'reason': reason},
            level='warning'
        )

    def log_account_deletion(self, user_id, email):
        """Log account deletion"""
        self.log_event(
            'account_deletion',
            user_id=user_id,
            details={'email': email},
            level='warning'
        )

    def log_csrf_failure(self):
        """Log CSRF token validation failure"""
        self.log_event('csrf_failure', level='warning')

    def log_rate_limit_exceeded(self, endpoint):
        """Log rate limit exceeded"""
        self.log_event(
            'rate_limit_exceeded',
            details={'endpoint': endpoint},
            level='warning'
        )

    def log_share_link_generated(self, user_id, version_id):
        """Log share link generation"""
        self.log_event(
            'share_link_generated',
            user_id=user_id,
            details={'version_id': version_id}
        )

    def log_unauthorized_access_attempt(self, user_id, resource_type, resource_id):
        """Log attempt to access unauthorized resource"""
        self.log_event(
            'unauthorized_access',
            user_id=user_id,
            details={
                'resource_type': resource_type,
                'resource_id': resource_id
            },
            level='warning'
        )

    def log_content_size_exceeded(self, user_id, size):
        """Log content size limit exceeded"""
        self.log_event(
            'content_size_exceeded',
            user_id=user_id,
            details={'size_bytes': size},
            level='warning'
        )

    def log_version_limit_exceeded(self, user_id, draft_id):
        """Log version limit exceeded"""
        self.log_event(
            'version_limit_exceeded',
            user_id=user_id,
            details={'draft_id': draft_id},
            level='warning'
        )

    def log_draft_limit_exceeded(self, user_id):
        """Log draft limit exceeded"""
        self.log_event(
            'draft_limit_exceeded',
            user_id=user_id,
            level='warning'
        )


# Create a global instance
security_logger = SecurityLogger()
