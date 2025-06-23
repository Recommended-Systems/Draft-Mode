from functools import wraps
from flask import session, redirect, url_for, request, flash
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

def get_current_user():
    """Get the current authenticated user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None