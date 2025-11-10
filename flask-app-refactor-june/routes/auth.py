from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User
from utils.decorators import redirect_if_authenticated
from utils.password_validator import validate_password_strength

auth_bp = Blueprint('auth', __name__)


def get_security_logger():
    """Get security logger instance"""
    return current_app.security_logger


def get_limiter():
    """Get limiter instance"""
    return current_app.limiter


@auth_bp.route('/signup', methods=['GET', 'POST'])
@redirect_if_authenticated
def signup():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Validation
        if not all([name, email, password]):
            flash('All fields are required')
            return render_template('signup.html')

        # Validate password strength
        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            for error in errors:
                flash(error)
            return render_template('signup.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Log the attempt
            get_security_logger().log_signup_attempt_existing_email(email)

            # Don't reveal that email exists - show generic message
            # In production, consider sending an email to the existing user warning them of the attempt
            flash('If this email is not already registered, you will receive a confirmation email shortly.')
            return redirect(url_for('auth.login'))
        
        # Create new user
        user = User(name=name, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()

            # Log successful signup
            get_security_logger().log_signup(user.id, email)

            # Regenerate session to prevent fixation
            session.clear()

            # Log them in
            session['user_id'] = user.id
            session.permanent = True
            session.modified = True
            flash('Account created successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account')
            return render_template('signup.html')
    
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@redirect_if_authenticated
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Log successful login
            get_security_logger().log_login_success(user.id, email)

            # Regenerate session to prevent fixation
            old_session_data = dict(session)
            session.clear()

            # Restore any safe data (like next page)
            if 'next' in old_session_data:
                session['next'] = old_session_data['next']

            # Log them in with new session
            session['user_id'] = user.id
            session.permanent = True
            session.modified = True
            flash('Welcome back!', 'success')

            # Redirect to intended page or dashboard
            next_page = request.args.get('next') or session.pop('next', None)
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            # Log failed login attempt
            get_security_logger().log_login_failure(email)
            flash('Invalid email or password')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    # Log the logout
    user_id = session.get('user_id')
    if user_id:
        get_security_logger().log_logout(user_id)

    # Clear session completely
    session.clear()

    # Force session regeneration
    session.modified = True

    flash('You have been logged out', 'success')
    return redirect(url_for('main.index'))