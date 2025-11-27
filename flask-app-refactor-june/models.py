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

    # Account lockout fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)

    # Password reset fields
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    # API token field
    api_token = db.Column(db.String(64), unique=True, nullable=True)
    api_token_created = db.Column(db.DateTime, nullable=True)

    # Relationships
    blog_drafts = db.relationship('BlogDraft', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    # Account lockout methods
    def is_locked(self):
        """Check if account is currently locked"""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def record_failed_login(self):
        """Record a failed login attempt and lock if threshold exceeded"""
        from datetime import timedelta
        self.failed_login_attempts += 1

        # Lock account for 30 minutes after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

        db.session.commit()

    def reset_failed_attempts(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    # Email verification methods
    def generate_verification_token(self):
        """Generate email verification token"""
        from datetime import timedelta
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token

    def verify_email(self, token):
        """Verify email with token"""
        if not self.verification_token or self.verification_token != token:
            return False
        if datetime.utcnow() > self.verification_token_expires:
            return False
        self.email_verified = True
        self.verification_token = None
        self.verification_token_expires = None
        db.session.commit()
        return True

    # Password reset methods
    def generate_reset_token(self):
        """Generate password reset token"""
        from datetime import timedelta
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify password reset token"""
        if not self.reset_token or self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return True

    def reset_password(self, token, new_password):
        """Reset password with valid token"""
        if not self.verify_reset_token(token):
            return False
        self.set_password(new_password)
        self.reset_token = None
        self.reset_token_expires = None
        db.session.commit()
        return True

    # API token methods
    def generate_api_token(self):
        """Generate API token for programmatic access"""
        self.api_token = secrets.token_urlsafe(48)
        self.api_token_created = datetime.utcnow()
        db.session.commit()
        return self.api_token

    def revoke_api_token(self):
        """Revoke the current API token"""
        self.api_token = None
        self.api_token_created = None
        db.session.commit()
    
    @property
    def total_drafts(self):
        """Get total number of drafts for this user"""
        return len(self.blog_drafts)
    
    @property
    def total_versions(self):
        """Get total number of versions across all drafts"""
        return sum(len(draft.versions) for draft in self.blog_drafts)
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_drafts': self.total_drafts,
            'total_versions': self.total_versions
        }
    
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
        return any(version.tag == 'final' for version in self.versions)
    
    @property
    def status(self):
        """Get draft status based on versions"""
        if not self.versions:
            return 'empty'
        elif self.has_final_version:
            return 'final'
        else:
            return 'active'
    
    def to_dict(self):
        """Convert draft to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'has_final_version': self.has_final_version,
            'version_count': len(self.versions) if self.versions else 0
        }
    
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
    share_token_expires = db.Column(db.DateTime, nullable=True)
    tag = db.Column(db.String(50), default='draft')  # New tag field: draft, final, ready_for_review, working

    def generate_share_token(self, expires_in_days=30):
        """Generate a unique share token for public access"""
        from datetime import timedelta
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
        # Always update expiration date
        self.share_token_expires = datetime.utcnow() + timedelta(days=expires_in_days)

    def is_share_token_valid(self):
        """Check if share token is still valid"""
        if not self.share_token:
            return False
        if not self.share_token_expires:
            return True  # Tokens created before expiration feature
        return datetime.utcnow() < self.share_token_expires
    
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
        return self.tag == 'final'
    
    @property
    def display_name(self):
        """Get display name with tag if not draft"""
        if not self.tag or self.tag == 'draft':
            return self.version_name
        else:
            tag_display = {
                'final': 'FINAL',
                'ready_for_review': 'REVIEW', 
                'working': 'WORKING'
            }.get(self.tag, self.tag.upper())
            return f"{self.version_name} [{tag_display}]"
    
    def set_as_current(self):
        """Set this version as the current one"""
        # Unset other current versions for this draft
        DraftVersion.query.filter_by(blog_draft_id=self.blog_draft_id, is_current=True).update({'is_current': False})
        self.is_current = True
        db.session.commit()
    
    def set_tag(self, new_tag):
        """Set tag and ensure uniqueness for special tags"""
        if new_tag in ['final', 'ready_for_review', 'working']:
            # Remove this tag from other versions in the same draft
            DraftVersion.query.filter_by(blog_draft_id=self.blog_draft_id, tag=new_tag).update({'tag': 'draft'})
        self.tag = new_tag
        db.session.commit()
    
    def to_dict(self):
        """Convert version to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'version_name': self.version_name,
            'content': self.content,
            'blog_draft_id': self.blog_draft_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_current': self.is_current,
            'share_token': self.share_token,
            'tag': self.tag,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'is_final': self.is_final,
            'display_name': self.display_name
        }
    
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

class PublishingPlatform(db.Model):
    """Store encrypted API credentials for publishing platforms"""
    __tablename__ = 'publishing_platforms'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform_type = db.Column(db.String(50), nullable=False)  # 'ghost', 'substack', 'buttondown', 'beehiiv'
    platform_url = db.Column(db.String(255))  # Ghost admin URL, etc.
    encrypted_api_key = db.Column(db.Text, nullable=False)  # Encrypted API key
    platform_config = db.Column(db.Text)  # JSON for additional platform-specific settings
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref=db.backref('publishing_platforms', lazy=True))

    def __repr__(self):
        return f'<PublishingPlatform {self.platform_type} for user {self.user_id}>'