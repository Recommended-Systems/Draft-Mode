from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User
from utils.decorators import redirect_if_authenticated
from utils.password_validator import validate_password_strength
from utils.input_validator import sanitize_text_input, validate_email, validate_name

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
        # Sanitize inputs
        name = sanitize_text_input(request.form.get('name', ''), max_length=100)
        email = sanitize_text_input(request.form.get('email', ''), max_length=120).lower()
        password = request.form.get('password', '')

        # Validation
        if not all([name, email, password]):
            flash('All fields are required')
            return render_template('signup.html')

        # Validate name
        is_valid_name, name_error = validate_name(name)
        if not is_valid_name:
            flash(name_error)
            return render_template('signup.html')

        # Validate email
        if not validate_email(email):
            flash('Invalid email address')
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
        # Sanitize inputs
        email = sanitize_text_input(request.form.get('email', ''), max_length=120).lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()

        # Check if account is locked
        if user and user.is_locked():
            flash('Account temporarily locked due to multiple failed login attempts. Please try again later.')
            return render_template('login.html')

        if user and user.check_password(password):
            # Reset failed login attempts on successful login
            user.reset_failed_attempts()

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
            # Record failed attempt if user exists
            if user:
                user.record_failed_login()

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


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify user email with token"""
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        flash('Invalid or expired verification link')
        return redirect(url_for('main.index'))

    if user.verify_email(token):
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Invalid or expired verification link')
        return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = sanitize_text_input(request.form.get('email', ''), max_length=120).lower()

        if not email:
            flash('Email is required')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()

        # Always show success message to prevent user enumeration
        flash('If an account exists with that email, you will receive password reset instructions.', 'success')

        if user:
            # Generate reset token
            reset_token = user.generate_reset_token()

            # Send reset email
            from utils.email_service import email_service
            try:
                print(f"\n[DEBUG] Attempting to send password reset email to {user.email}", flush=True)
                email_service.send_password_reset_email(user, reset_token)
                print(f"[DEBUG] Email send completed", flush=True)
            except Exception as e:
                print(f"[ERROR] Failed to send password reset email: {e}", flush=True)
                current_app.logger.error(f"Failed to send password reset email: {e}")
                import traceback
                traceback.print_exc()

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset link')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or not confirm_password:
            flash('Please enter and confirm your password')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('reset_password.html', token=token)

        # Validate password strength
        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            for error in errors:
                flash(error)
            return render_template('reset_password.html', token=token)

        # Reset the password
        if user.reset_password(token, password):
            # Send confirmation email
            from utils.email_service import email_service
            try:
                email_service.send_password_changed_notification(user)
            except Exception as e:
                current_app.logger.error(f"Failed to send password changed email: {e}")

            flash('Password reset successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Failed to reset password. Please try again.')
            return redirect(url_for('auth.forgot_password'))

    return render_template('reset_password.html', token=token)