from functools import wraps
from flask import session, redirect, url_for, request, flash, jsonify, g
from models import User


def login_required(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Store the intended destination
            if request.endpoint != 'auth.login':
                session['next'] = request.url
            flash('Please log in to access this page.')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def redirect_if_authenticated(f):
    """Decorator to redirect authenticated users away from auth pages"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f):
    """Decorator to require API key authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        user = User.query.filter_by(api_token=api_key).first()

        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Make user available to route via flask.g
        g.current_user = user

        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the current authenticated user"""
    # Check if user is set via API key (in flask.g)
    if hasattr(g, 'current_user'):
        return g.current_user

    # Check session-based authentication
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        # If user doesn't exist (e.g., database was reset), clear the session
        if not user:
            session.clear()
            return None
        return user

    return None