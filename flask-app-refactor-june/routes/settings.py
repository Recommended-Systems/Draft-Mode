from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User
from utils.decorators import login_required, get_current_user

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and settings page"""
    user = get_current_user()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email]):
            flash('Name and email are required')
            return render_template('settings/profile.html', user=user)
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash('Email already registered to another account')
            return render_template('settings/profile.html', user=user)
        
        # Password change validation
        if new_password:
            if not current_password:
                flash('Current password is required to change password')
                return render_template('settings/profile.html', user=user)
            
            if not user.check_password(current_password):
                flash('Current password is incorrect')
                return render_template('settings/profile.html', user=user)
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long')
                return render_template('settings/profile.html', user=user)
            
            if new_password != confirm_password:
                flash('New passwords do not match')
                return render_template('settings/profile.html', user=user)
        
        try:
            # Update user information
            user.name = name
            user.email = email
            
            # Update password if provided
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('settings.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile')
            return render_template('settings/profile.html', user=user)
    
    return render_template('settings/profile.html', user=user)

@settings_bp.route('/theme', methods=['POST'])
@login_required
def update_theme():
    """Update user theme preference"""
    theme = request.json.get('theme', 'light')
    
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'error': 'Invalid theme'})
    
    # Store theme preference in session
    session['theme'] = theme
    session.permanent = True
    
    return jsonify({'success': True, 'theme': theme})

@settings_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (with confirmation)"""
    user = get_current_user()
    password = request.form.get('password', '')
    
    if not password:
        flash('Password is required to delete account')
        return redirect(url_for('settings.profile'))
    
    if not user.check_password(password):
        flash('Incorrect password')
        return redirect(url_for('settings.profile'))
    
    try:
        # This will cascade delete all drafts and versions due to the relationship setup
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash('Your account has been deleted', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting your account')
        return redirect(url_for('settings.profile'))