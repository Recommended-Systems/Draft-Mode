"""Rate limiting utilities for routes"""
from functools import wraps
from flask import current_app, request
from flask_limiter.util import get_remote_address


def get_limiter():
    """Get the limiter instance from the current app"""
    return current_app.limiter


def apply_rate_limit(limit_string):
    """
    Manually apply rate limit within a route function
    Usage:
        apply_rate_limit("5 per minute")
    """
    limiter = get_limiter()
    key = get_remote_address()

    # Check if limit is exceeded
    if not limiter.check():
        limiter.hit()
        from flask_limiter.errors import RateLimitExceeded
        raise RateLimitExceeded(f"Rate limit exceeded: {limit_string}")

    limiter.hit()
