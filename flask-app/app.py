from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import markdown
from markupsafe import Markup

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)