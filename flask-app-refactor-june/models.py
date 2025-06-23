from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

# Import db from the main app module
from flask import current_app
from sqlalchemy import event

# We'll define db here and import it in app.py
db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and draft ownership"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    blog_drafts = db.relationship('BlogDraft', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def total_drafts(self):
        """Get total number of drafts for this user"""
        return len(self.blog_drafts)
    
    @property
    def total_versions(self):
        """Get total number of versions across all drafts"""
        return sum(len(draft.versions) for draft in self.blog_drafts)
    
    def __repr__(self):
        return f'<User {self.email}>'

class BlogDraft(db.Model):
    """Blog draft model to organize multiple versions"""
    __tablename__ = 'blog_drafts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = db.relationship('DraftVersion', backref='blog_draft', lazy=True, cascade='all, delete-orphan', order_by='DraftVersion.created_at.desc()')
    
    @property
    def current_version(self):
        """Get the current active version"""
        current = DraftVersion.query.filter_by(blog_draft_id=self.id, is_current=True).first()
        if not current and self.versions:
            # If no current version is set, return the latest one
            current = self.versions[0]  # versions are ordered by created_at desc in relationship
        return current
    
    @property
    def latest_version(self):
        """Get the most recently created version"""
        return DraftVersion.query.filter_by(blog_draft_id=self.id).order_by(DraftVersion.created_at.desc()).first()
    
    @property
    def has_final_version(self):
        """Check if any version is marked as final"""
        return any('final' in version.version_name.lower() or 'published' in version.version_name.lower() 
                  for version in self.versions)
    
    @property
    def status(self):
        """Get draft status based on versions"""
        if not self.versions:
            return 'empty'
        elif self.has_final_version:
            return 'final'
        else:
            return 'active'
    
    def __repr__(self):
        return f'<BlogDraft {self.title}>'

class DraftVersion(db.Model):
    """Individual version of a blog draft"""
    __tablename__ = 'draft_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    version_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False, default='')
    blog_draft_id = db.Column(db.Integer, db.ForeignKey('blog_drafts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_current = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(32), unique=True, nullable=True, index=True)
    
    def generate_share_token(self):
        """Generate a unique share token for public access"""
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
    
    @property
    def word_count(self):
        """Get word count for this version"""
        return len(self.content.split()) if self.content else 0
    
    @property
    def character_count(self):
        """Get character count for this version"""
        return len(self.content) if self.content else 0
    
    @property
    def is_final(self):
        """Check if this version is marked as final"""
        return 'final' in self.version_name.lower() or 'published' in self.version_name.lower()
    
    def set_as_current(self):
        """Set this version as the current one"""
        # Unset other current versions for this draft
        DraftVersion.query.filter_by(blog_draft_id=self.blog_draft_id, is_current=True).update({'is_current': False})
        self.is_current = True
        db.session.commit()
    
    def __repr__(self):
        return f'<DraftVersion {self.version_name} for {self.blog_draft.title}>'

# Database event listeners
@event.listens_for(DraftVersion, 'after_insert')
def set_first_version_as_current(mapper, connection, target):
    """Automatically set the first version as current"""
    if not target.is_current:
        # Check if this is the first version for this draft
        version_count = connection.execute(
            db.text("SELECT COUNT(*) FROM draft_versions WHERE blog_draft_id = :draft_id"),
            {"draft_id": target.blog_draft_id}
        ).scalar()
        
        if version_count == 1:
            connection.execute(
                db.text("UPDATE draft_versions SET is_current = 1 WHERE id = :version_id"),
                {"version_id": target.id}
            )

@event.listens_for(DraftVersion, 'after_update')
def update_draft_timestamp(mapper, connection, target):
    """Update parent draft's updated_at when version changes"""
    connection.execute(
        db.text("UPDATE blog_drafts SET updated_at = :now WHERE id = :draft_id"),
        {"now": datetime.utcnow(), "draft_id": target.blog_draft_id}
    )