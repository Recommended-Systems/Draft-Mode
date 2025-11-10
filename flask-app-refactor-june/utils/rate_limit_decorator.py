"""Rate limiting decorators"""
from functools import wraps
from flask import current_app, request, flash, jsonify
from flask_limiter.errors import RateLimitExceeded


def rate_limit(limit_value):
    """
    Apply rate limit to a route

    Usage:
        @rate_limit("5 per minute")
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = current_app.limiter

            # Create a key for this specific route
            key_func = lambda: f"{request.remote_addr}:{request.endpoint}"

            try:
                # Apply the limit
                with limiter.limit(limit_value, key_func=key_func):
                    return f(*args, **kwargs)
            except RateLimitExceeded:
                # Log the rate limit violation
                if hasattr(current_app, 'security_logger'):
                    current_app.security_logger.log_rate_limit_exceeded(request.endpoint)

                # Return appropriate response
                if request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Rate limit exceeded. Please try again later.',
                        'limit': limit_value
                    }), 429
                else:
                    flash('Too many requests. Please try again later.')
                    # Return to the same page with 429 status
                    return current_app.make_response(('', 429))

        return decorated_function
    return decorator
