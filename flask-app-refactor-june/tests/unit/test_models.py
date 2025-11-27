"""
Unit tests for database models
Tests model methods, relationships, and validation
"""
import pytest
from models import User, BlogDraft, DraftVersion, PublishingPlatform
from datetime import datetime

class TestUserModel:
    """Test User model"""

    def test_create_user(self, init_database):
        """Test user creation"""
        user = User(name='testuser', email='test@example.com')
        user.set_password('password123')
        init_database.session.add(user)
        init_database.session.commit()

        assert user.id is not None
        assert user.name == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash is not None
        assert user.password_hash != 'password123'

    def test_password_hashing(self, init_database):
        """Test password hashing and verification"""
        user = User(name='testuser', email='test@example.com')
        user.set_password('SecurePassword123!')

        # Password should be hashed
        assert user.password_hash != 'SecurePassword123!'

        # Correct password should verify
        assert user.check_password('SecurePassword123!') is True

        # Incorrect password should not verify
        assert user.check_password('WrongPassword') is False

    def test_unique_username(self, init_database, test_user):
        """Test username uniqueness constraint"""
        duplicate_user = User(
            name='testuser',  # Same as test_user
            email='different@example.com'
        )
        init_database.session.add(duplicate_user)

        with pytest.raises(Exception):  # IntegrityError
            init_database.session.commit()

    def test_unique_email(self, init_database, test_user):
        """Test email uniqueness constraint"""
        duplicate_user = User(
            name='different',
            email='test@example.com'  # Same as test_user
        )
        init_database.session.add(duplicate_user)

        with pytest.raises(Exception):  # IntegrityError
            init_database.session.commit()

    def test_user_drafts_relationship(self, init_database, test_user, test_draft):
        """Test user-drafts relationship"""
        assert len(test_user.blog_drafts) == 1
        assert test_user.blog_drafts[0].id == test_draft.id
        assert test_user.blog_drafts[0].title == 'Test Draft'

    def test_user_verification(self, init_database):
        """Test user verification fields"""
        user = User(name='newuser', email='new@example.com')
        user.set_password('password')

        # User should not be verified by default
        assert user.email_verified is False
        assert user.verification_token is None

        # Generate verification token
        user.verification_token = 'test-token'
        init_database.session.add(user)
        init_database.session.commit()

        assert user.verification_token == 'test-token'


class TestBlogDraftModel:
    """Test BlogDraft model"""

    def test_create_draft(self, init_database, test_user):
        """Test draft creation"""
        draft = BlogDraft(
            title='New Draft',
            description='Draft description',
            user_id=test_user.id
        )
        init_database.session.add(draft)
        init_database.session.commit()

        assert draft.id is not None
        assert draft.title == 'New Draft'
        assert draft.user_id == test_user.id
        assert draft.created_at is not None
        assert draft.updated_at is not None

    def test_draft_user_relationship(self, init_database, test_draft, test_user):
        """Test draft-user relationship"""
        assert test_draft.author.id == test_user.id
        assert test_draft.author.name == 'testuser'

    def test_draft_versions_relationship(self, init_database, test_draft):
        """Test draft-versions relationship"""
        assert len(test_draft.versions) == 1
        assert test_draft.versions[0].version_name == 'v1.0'

    def test_draft_cascade_delete(self, init_database, test_user, test_draft):
        """Test that deleting draft deletes versions"""
        draft_id = test_draft.id
        version_id = test_draft.versions[0].id

        init_database.session.delete(test_draft)
        init_database.session.commit()

        # Draft should be deleted
        assert BlogDraft.query.get(draft_id) is None

        # Versions should also be deleted (cascade)
        assert DraftVersion.query.get(version_id) is None


class TestDraftVersionModel:
    """Test DraftVersion model"""

    def test_create_version(self, init_database, test_draft):
        """Test version creation"""
        version = DraftVersion(
            version_name='v2.0',
            content='New content',
            blog_draft_id=test_draft.id,
            is_current=False,
            tag='draft'
        )
        init_database.session.add(version)
        init_database.session.commit()

        assert version.id is not None
        assert version.version_name == 'v2.0'
        assert version.blog_draft_id == test_draft.id

    def test_version_draft_relationship(self, init_database, test_draft):
        """Test version-draft relationship"""
        version = test_draft.versions[0]
        assert version.blog_draft.id == test_draft.id
        assert version.blog_draft.title == 'Test Draft'

    def test_current_version(self, init_database, test_draft_with_versions):
        """Test current version flag"""
        current_versions = [v for v in test_draft_with_versions.versions if v.is_current]
        assert len(current_versions) == 1
        assert current_versions[0].version_name == 'v3.0'

    def test_version_tags(self, init_database, test_draft):
        """Test version tags"""
        valid_tags = ['draft', 'working', 'ready_for_review', 'final']

        for tag in valid_tags:
            version = DraftVersion(
                version_name=f'v-{tag}',
                content='Content',
                blog_draft_id=test_draft.id,
                tag=tag
            )
            init_database.session.add(version)

        init_database.session.commit()

        # All versions should be created successfully
        assert len(test_draft.versions) == 5  # 1 original + 4 new


class TestPublishingPlatformModel:
    """Test PublishingPlatform model"""

    def test_create_platform(self, init_database, test_user):
        """Test publishing platform creation"""
        platform = PublishingPlatform(
            user_id=test_user.id,
            platform_type='ghost',
            platform_url='https://example.ghost.io',
            encrypted_api_key='encrypted-key',
            is_active=True
        )
        init_database.session.add(platform)
        init_database.session.commit()

        assert platform.id is not None
        assert platform.platform_type == 'ghost'
        assert platform.is_active is True

    def test_platform_user_relationship(self, init_database, ghost_platform, test_user):
        """Test platform-user relationship"""
        assert ghost_platform.user.id == test_user.id
        assert len(test_user.publishing_platforms) == 1

    def test_platform_types(self, init_database, test_user):
        """Test different platform types"""
        platforms = ['ghost', 'substack', 'buttondown', 'beehiiv']

        for platform_type in platforms:
            platform = PublishingPlatform(
                user_id=test_user.id,
                platform_type=platform_type,
                encrypted_api_key='key',
                is_active=True
            )
            init_database.session.add(platform)

        init_database.session.commit()

        # All platform types should be created
        assert len(test_user.publishing_platforms) == len(platforms)

    def test_platform_deactivation(self, init_database, ghost_platform):
        """Test platform deactivation"""
        assert ghost_platform.is_active is True

        ghost_platform.is_active = False
        init_database.session.commit()

        # Platform should be inactive
        reloaded = PublishingPlatform.query.get(ghost_platform.id)
        assert reloaded.is_active is False

    def test_last_used_timestamp(self, init_database, ghost_platform):
        """Test last_used_at timestamp update"""
        assert ghost_platform.last_used_at is None

        ghost_platform.last_used_at = datetime.utcnow()
        init_database.session.commit()

        assert ghost_platform.last_used_at is not None
