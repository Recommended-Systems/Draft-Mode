from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import markdown
from markupsafe import Markup
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///draft_mode.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to blog drafts
    blog_drafts = db.relationship('BlogDraft', backref='author', lazy=True, cascade='all, delete-orphan')

class BlogDraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to versions
    versions = db.relationship('DraftVersion', backref='blog_draft', lazy=True, cascade='all, delete-orphan')

class DraftVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False, default='')
    blog_draft_id = db.Column(db.Integer, db.ForeignKey('blog_draft.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_current = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(32), unique=True, nullable=True)  # For public sharing

# Helper functions
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('signup.html')
        
        # Create new user
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        # Log them in
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    drafts = BlogDraft.query.filter_by(user_id=user.id).order_by(BlogDraft.updated_at.desc()).all()
    return render_template('dashboard.html', user=user, drafts=drafts)

@app.route('/create_draft', methods=['GET', 'POST'])
@login_required
def create_draft():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        
        user = get_current_user()
        draft = BlogDraft(
            title=title,
            description=description,
            user_id=user.id
        )
        db.session.add(draft)
        db.session.commit()
        
        # Create initial version
        version = DraftVersion(
            version_name='v1.0',
            content='# ' + title + '\n\nStart writing your blog post here...',
            blog_draft_id=draft.id,
            is_current=True
        )
        db.session.add(version)
        db.session.commit()
        
        return redirect(url_for('edit_draft', draft_id=draft.id))
    
    return render_template('create_draft.html')

@app.route('/draft/<int:draft_id>')
@login_required
def edit_draft(draft_id):
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    # Check if specific version requested
    version_id = request.args.get('version')
    if version_id:
        current_version = DraftVersion.query.filter_by(
            id=version_id, 
            blog_draft_id=draft.id
        ).first()
        if current_version:
            # Update current version flag
            DraftVersion.query.filter_by(blog_draft_id=draft.id, is_current=True).update({'is_current': False})
            current_version.is_current = True
            db.session.commit()
    else:
        # Get current version or latest version
        current_version = DraftVersion.query.filter_by(blog_draft_id=draft.id, is_current=True).first()
        if not current_version:
            current_version = DraftVersion.query.filter_by(blog_draft_id=draft.id).order_by(DraftVersion.created_at.desc()).first()
    
    versions = DraftVersion.query.filter_by(blog_draft_id=draft.id).order_by(DraftVersion.created_at.desc()).all()
    
    return render_template('edit_draft.html', draft=draft, current_version=current_version, versions=versions)

@app.route('/create_version/<int:draft_id>', methods=['POST'])
@login_required
def create_version(draft_id):
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    version_name = request.form['version_name']
    content = request.form.get('content', '')
    
    # Unset current version
    DraftVersion.query.filter_by(blog_draft_id=draft.id, is_current=True).update({'is_current': False})
    
    # Create new version
    version = DraftVersion(
        version_name=version_name,
        content=content,
        blog_draft_id=draft.id,
        is_current=True
    )
    db.session.add(version)
    db.session.commit()
    
    return jsonify({'success': True, 'version_id': version.id})

@app.route('/save_version/<int:version_id>', methods=['POST'])
@login_required
def save_version(version_id):
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    content = request.json.get('content', '')
    version.content = content
    version.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/preview/<int:version_id>', methods=['POST'])
@login_required
def preview_version(version_id):
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    # Get content from request if provided, otherwise use saved content
    content = request.json.get('content', version.content) if request.is_json else version.content
    
    try:
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite', 'fenced_code'])
    except:
        # Fallback to basic markdown if extensions fail
        html_content = markdown.markdown(content)
    
    return jsonify({'html': html_content})

@app.route('/preview_content', methods=['POST'])
@login_required
def preview_content():
    """Preview content without needing a specific version ID"""
    content = request.json.get('content', '') if request.is_json else ''
    
    try:
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite', 'fenced_code'])
    except:
        # Fallback to basic markdown if extensions fail
        html_content = markdown.markdown(content)
    
    return jsonify({'html': html_content})

@app.route('/compare/<int:version1_id>/<int:version2_id>')
@login_required
def compare_versions(version1_id, version2_id):
    user = get_current_user()
    
    version1 = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version1_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    version2 = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version2_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    return render_template('compare.html', 
                         draft=version1.blog_draft,
                         version1=version1, 
                         version2=version2)

# NEW ROUTES FOR ENHANCED FUNCTIONALITY

@app.route('/rename_draft/<int:draft_id>', methods=['POST'])
@login_required
def rename_draft(draft_id):
    """Rename a blog draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    new_name = request.json.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Name cannot be empty'})
    
    draft.title = new_name
    draft.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/rename_version/<int:version_id>', methods=['POST'])
@login_required
def rename_version(version_id):
    """Rename a draft version"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    new_name = request.json.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Name cannot be empty'})
    
    version.version_name = new_name
    version.updated_at = datetime.utcnow()
    
    # Update the parent draft's updated_at timestamp
    version.blog_draft.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/mark_final/<int:version_id>', methods=['POST'])
@login_required
def mark_final(version_id):
    """Mark a version as final/published"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    final_name = request.json.get('name', '').strip()
    if not final_name:
        return jsonify({'success': False, 'error': 'Final name cannot be empty'})
    
    # Update version name to indicate it's final
    version.version_name = final_name
    version.updated_at = datetime.utcnow()
    
    # Generate a share token if it doesn't exist
    if not version.share_token:
        version.share_token = secrets.token_urlsafe(16)
    
    # Update the parent draft's updated_at timestamp
    version.blog_draft.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_version/<int:version_id>', methods=['POST'])
@login_required
def delete_version(version_id):
    """Delete a draft version (with safety checks)"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    # Check if this is the only version
    version_count = DraftVersion.query.filter_by(blog_draft_id=version.blog_draft_id).count()
    if version_count <= 1:
        return jsonify({'success': False, 'error': 'Cannot delete the only version of a draft'})
    
    # If this is the current version, set another version as current
    if version.is_current:
        other_version = DraftVersion.query.filter(
            DraftVersion.blog_draft_id == version.blog_draft_id,
            DraftVersion.id != version.id
        ).order_by(DraftVersion.created_at.desc()).first()
        
        if other_version:
            other_version.is_current = True
    
    # Update the parent draft's updated_at timestamp
    version.blog_draft.updated_at = datetime.utcnow()
    
    db.session.delete(version)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_draft/<int:draft_id>', methods=['POST'])
@login_required
def delete_draft(draft_id):
    """Delete an entire draft and all its versions"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    # This will cascade delete all versions due to the relationship setup
    db.session.delete(draft)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/duplicate_version/<int:version_id>', methods=['POST'])
@login_required
def duplicate_version(version_id):
    """Create a duplicate of an existing version"""
    user = get_current_user()
    original_version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    new_name = request.json.get('name', f"{original_version.version_name} (Copy)")
    
    # Unset current version flag from other versions
    DraftVersion.query.filter_by(
        blog_draft_id=original_version.blog_draft_id, 
        is_current=True
    ).update({'is_current': False})
    
    # Create duplicate version
    duplicate = DraftVersion(
        version_name=new_name,
        content=original_version.content,
        blog_draft_id=original_version.blog_draft_id,
        is_current=True
    )
    
    db.session.add(duplicate)
    
    # Update the parent draft's updated_at timestamp
    original_version.blog_draft.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'version_id': duplicate.id})

@app.route('/api/drafts/<int:draft_id>/stats')
@login_required
def get_draft_stats(draft_id):
    """Get statistics for a specific draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    versions = DraftVersion.query.filter_by(blog_draft_id=draft.id).all()
    
    total_words = 0
    total_chars = 0
    
    for version in versions:
        # Simple word and character count
        words = len(version.content.split())
        chars = len(version.content)
        total_words += words
        total_chars += chars
    
    current_version = next((v for v in versions if v.is_current), versions[0] if versions else None)
    current_words = len(current_version.content.split()) if current_version else 0
    current_chars = len(current_version.content) if current_version else 0
    
    stats = {
        'draft_id': draft.id,
        'title': draft.title,
        'total_versions': len(versions),
        'total_words_all_versions': total_words,
        'total_chars_all_versions': total_chars,
        'current_version_words': current_words,
        'current_version_chars': current_chars,
        'created_at': draft.created_at.isoformat(),
        'updated_at': draft.updated_at.isoformat(),
        'has_final_version': any('final' in v.version_name.lower() or 'published' in v.version_name.lower() for v in versions)
    }
    
    return jsonify(stats)

# NEW ROUTE FOR PUBLIC SHARING
@app.route('/share/<share_token>')
def public_view(share_token):
    """View a publicly shared version without authentication"""
    version = DraftVersion.query.filter_by(share_token=share_token).first_or_404()
    
    try:
        html_content = markdown.markdown(version.content, extensions=['extra', 'codehilite', 'fenced_code'])
    except:
        html_content = markdown.markdown(version.content)
    
    return render_template('public_view.html', 
                         version=version, 
                         draft=version.blog_draft,
                         author=version.blog_draft.author,
                         html_content=Markup(html_content))

@app.route('/generate_share_link/<int:version_id>', methods=['POST'])
@login_required
def generate_share_link(version_id):
    """Generate a public share link for a version"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    # Generate share token if it doesn't exist
    if not version.share_token:
        version.share_token = secrets.token_urlsafe(16)
        db.session.commit()
    
    share_url = url_for('public_view', share_token=version.share_token, _external=True)
    return jsonify({'success': True, 'share_url': share_url})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)