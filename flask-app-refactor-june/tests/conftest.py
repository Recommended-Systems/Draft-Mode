"""
Pytest configuration and fixtures for testing
Provides reusable test fixtures for database, app, client, and test data
"""
import pytest
import os
from app import create_app
from models import db, User, BlogDraft, DraftVersion, PublishingPlatform
from datetime import datetime
from utils.encryption import encrypt_api_key

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Set testing environment variable
    os.environ['FLASK_ENV'] = 'testing'

    app = create_app('testing')

    # Ensure testing configuration
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENCRYPTION_KEY': 'ytZHmtDrQh42yoHmqmm8pxXaw9PFcFBHPGETxdVk62c=',  # Valid Fernet key for testing
        'SERVER_NAME': 'localhost.localdomain'
    })

    yield app

@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """Create CLI runner"""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def init_database(app):
    """Initialize database for each test"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(init_database):
    """Create a test user"""
    user = User(
        name='testuser',
        email='test@example.com',
        email_verified=True
    )
    user.set_password('TestPassword123!')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def second_user(init_database):
    """Create a second test user for multi-user tests"""
    user = User(
        name='testuser2',
        email='test2@example.com',
        email_verified=True
    )
    user.set_password('TestPassword123!')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def unverified_user(init_database):
    """Create an unverified test user"""
    user = User(
        name='unverified',
        email='unverified@example.com',
        email_verified=False
    )
    user.set_password('TestPassword123!')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authenticated session"""
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
    return client

@pytest.fixture
def test_draft(init_database, test_user):
    """Create a test draft with initial version"""
    draft = BlogDraft(
        title='Test Draft',
        description='Test Description',
        user_id=test_user.id
    )
    db.session.add(draft)
    db.session.commit()

    # Create initial version
    version = DraftVersion(
        version_name='v1.0',
        content='# Test Content\n\nThis is a test draft.',
        blog_draft_id=draft.id,
        is_current=True,
        tag='draft'
    )
    db.session.add(version)
    db.session.commit()

    return draft

@pytest.fixture
def test_draft_with_versions(init_database, test_user):
    """Create a test draft with multiple versions"""
    draft = BlogDraft(
        title='Multi-Version Draft',
        description='Draft with multiple versions',
        user_id=test_user.id
    )
    db.session.add(draft)
    db.session.commit()

    # Create multiple versions
    versions = []
    for i in range(3):
        version = DraftVersion(
            version_name=f'v{i+1}.0',
            content=f'# Version {i+1}\n\nContent for version {i+1}',
            blog_draft_id=draft.id,
            is_current=(i == 2),  # Last version is current
            tag='draft' if i < 2 else 'working'
        )
        db.session.add(version)
        versions.append(version)

    db.session.commit()
    draft.versions = versions
    return draft

@pytest.fixture
def ghost_platform(init_database, test_user):
    """Create a test Ghost publishing platform"""
    platform = PublishingPlatform(
        user_id=test_user.id,
        platform_type='ghost',
        platform_url='https://test.ghost.io',
        encrypted_api_key=encrypt_api_key('test-key-id:test-key-secret'),
        is_active=True
    )
    db.session.add(platform)
    db.session.commit()
    return platform

@pytest.fixture
def mock_ghost_response():
    """Mock successful Ghost API response"""
    return {
        'posts': [{
            'id': 'test-post-id',
            'title': 'Test Post',
            'url': 'https://test.ghost.io/test-post/',
            'status': 'draft'
        }]
    }

# Test data helpers
@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing"""
    return """# Sample Blog Post

This is a test blog post with **bold** and *italic* text.

## Section 1

- List item 1
- List item 2
- List item 3

## Section 2

```python
def hello_world():
    print("Hello, World!")
```

> This is a blockquote

[Link text](https://example.com)
"""

@pytest.fixture
def invalid_user_data():
    """Invalid user registration data for testing validation"""
    return {
        'username': 'ab',  # Too short
        'email': 'invalid-email',  # Invalid format
        'password': 'weak',  # Too weak
        'confirm_password': 'different'  # Doesn't match
    }

@pytest.fixture
def valid_user_data():
    """Valid user registration data"""
    return {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!'
    }
