# Testing Architecture & Implementation Guide

## Executive Summary

A comprehensive testing infrastructure has been implemented for Draft Mode to ensure:
- **Non-breaking changes**: Automated tests catch regressions before deployment
- **Resilience**: Edge cases and error conditions are validated
- **Maintainability**: Clear test patterns make adding new tests easy
- **Security**: Critical security features are thoroughly tested

## Quick Start

### 1. Install Testing Dependencies

```bash
# Install all testing tools
pip install -r requirements-test.txt

# Or use make command
make install-dev
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Or use make command
make test

# Quick test (no coverage)
make quick-test
```

### 3. View Coverage Report

```bash
make coverage
# Opens HTML coverage report in browser
```

## Testing Architecture

### 1. Test Structure

```
tests/
├── conftest.py                 # Shared fixtures (database, users, drafts)
├── unit/                       # Test individual components
│   ├── test_models.py         # 48 tests for database models
│   └── test_encryption.py     # 8 tests for encryption utilities
└── integration/                # Test complete workflows
    ├── test_auth.py           # 25 tests for authentication
    ├── test_drafts.py         # 30 tests for draft management
    └── test_publishing.py     # 20 tests for Ghost publishing
```

### 2. Test Coverage

**Current Test Count**: 131 tests across all modules

**Coverage by Module**:
- Models (User, BlogDraft, DraftVersion, PublishingPlatform): 48 tests
- Authentication (login, registration, sessions): 25 tests
- Draft Management (CRUD, versions): 30 tests
- Publishing (Ghost integration): 20 tests
- Encryption utilities: 8 tests

**Target Coverage**: 70% overall, 100% for critical paths

### 3. Key Testing Patterns

#### Pattern 1: Fixture-Based Test Data

```python
# tests/conftest.py defines reusable fixtures
@pytest.fixture
def test_user(init_database):
    """Pre-configured test user"""
    user = User(username='testuser', email='test@example.com')
    user.set_password('TestPassword123!')
    db.session.add(user)
    db.session.commit()
    return user

# Use in tests
def test_user_login(client, test_user):
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 200
```

#### Pattern 2: Mocking External Services

```python
from unittest.mock import patch, MagicMock

@patch('routes.publish.requests.post')
def test_ghost_publishing(mock_post, authenticated_client, test_draft):
    """Test Ghost API without making real HTTP requests"""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        'posts': [{'id': 'test-post-id'}]
    }
    mock_post.return_value = mock_response

    # Test the feature
    response = authenticated_client.post('/api/publish/ghost/1')
    assert response.status_code == 200
```

#### Pattern 3: Testing Both Success and Failure

```python
class TestUserRegistration:
    def test_successful_registration(self, client):
        """Test valid registration succeeds"""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        })
        assert response.status_code == 200

    def test_duplicate_username_fails(self, client, test_user):
        """Test duplicate username is rejected"""
        response = client.post('/auth/register', data={
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        })
        assert 'username' in response.data.lower()
```

## Running Tests in Different Scenarios

### Development Workflow

```bash
# Fast feedback during development
make quick-test

# Run specific test file
pytest tests/integration/test_publishing.py -v

# Run specific test
pytest tests/unit/test_models.py::TestUserModel::test_password_hashing -v

# Auto-rerun tests on file changes
pytest-watch
```

### Pre-Commit Checks

```bash
# Run all pre-commit checks
make pre-commit

# This runs:
# 1. Code formatting (black, isort)
# 2. Linting (flake8)
# 3. Fast tests
```

### CI/CD Pipeline

GitHub Actions automatically runs on every push:

1. **Test Suite**: Runs on Python 3.9, 3.10, 3.11
2. **Code Quality**: Checks formatting and linting
3. **Security**: Scans for vulnerabilities
4. **Coverage**: Reports coverage to Codecov

### Security Testing

```bash
# Check for known vulnerabilities
make security

# Full security audit
make security-audit
```

## Critical Test Areas

### 1. Authentication Security (100% Coverage Required)

**Why**: Security vulnerabilities can compromise user accounts

**Tests**:
- Password hashing and verification
- Session management
- Login attempt validation
- CSRF protection
- Unauthorized access prevention

**Example**:
```python
def test_password_hashing_is_secure(self, init_database):
    user = User(username='test', email='test@example.com')
    user.set_password('SecurePassword123!')

    # Password should be hashed, not stored in plaintext
    assert user.password_hash != 'SecurePassword123!'
    # Hashed password should verify correctly
    assert user.check_password('SecurePassword123!') is True
    # Wrong password should not verify
    assert user.check_password('WrongPassword') is False
```

### 2. Data Encryption (100% Coverage Required)

**Why**: API keys and sensitive data must be encrypted at rest

**Tests**:
- Encryption/decryption roundtrip
- Empty string handling
- Invalid data handling
- Key format validation

**Example**:
```python
def test_api_key_encryption_roundtrip(self, app):
    with app.app_context():
        original = 'secret-api-key-123'
        encrypted = encrypt_api_key(original)
        decrypted = decrypt_api_key(encrypted)

        # Should decrypt to original
        assert decrypted == original
        # Encrypted should be different
        assert encrypted != original
```

### 3. Publishing Integration (80% Coverage)

**Why**: Ensures reliable publishing to external platforms

**Tests**:
- Successful publishing
- API error handling
- Network failure recovery
- Authentication validation
- Multi-user isolation

**Example**:
```python
@patch('routes.publish.requests.post')
def test_ghost_api_error_handling(self, mock_post, authenticated_client, test_draft):
    # Mock API error
    mock_post.side_effect = Exception('Network timeout')

    response = authenticated_client.post('/api/publish/ghost/1')

    # Should handle error gracefully
    assert response.status_code == 500
    assert 'error' in response.json()
```

## Adding Tests for New Features

### Step 1: Identify Test Category

- **Unit Test**: Single function/method, no external dependencies
- **Integration Test**: Multiple components, database, or external services

### Step 2: Choose Fixtures

```python
# User-related features
def test_feature(test_user, authenticated_client):
    pass

# Draft-related features
def test_feature(test_draft, authenticated_client):
    pass

# Publishing features
def test_feature(ghost_platform, test_draft, authenticated_client):
    pass
```

### Step 3: Write Test Following AAA Pattern

```python
def test_new_feature(self, fixture1, fixture2):
    """Test description: what this test validates"""
    # Arrange: Set up test data
    data = {'key': 'value'}

    # Act: Execute the feature
    response = client.post('/endpoint', json=data)

    # Assert: Verify behavior
    assert response.status_code == 200
    assert response.json()['success'] is True
```

### Step 4: Test Edge Cases

```python
class TestNewFeature:
    def test_success_case(self):
        """Test normal operation"""
        pass

    def test_validation_error(self):
        """Test invalid input is rejected"""
        pass

    def test_authentication_required(self):
        """Test unauthenticated access is blocked"""
        pass

    def test_authorization_check(self):
        """Test users can't access other users' data"""
        pass
```

## Continuous Improvement

### Monitoring Test Health

```bash
# Check coverage percentage
pytest --cov=. --cov-report=term-missing

# Identify untested code
# Look for lines marked with "Missing" in coverage report
```

### Maintaining Test Quality

1. **Keep tests isolated**: Each test should clean up after itself
2. **Keep tests fast**: Mock external services, use in-memory database
3. **Keep tests readable**: Use descriptive names and clear assertions
4. **Keep tests current**: Update tests when features change

### When Tests Fail

1. **Read the error message**: Pytest provides detailed failure info
2. **Run with verbose output**: `pytest -vv -s`
3. **Use debugger**: `pytest --pdb`
4. **Check fixtures**: Ensure test data is set up correctly

## Example: Adding Tests for New Feature

Suppose you're adding a "Draft Templates" feature:

### 1. Create Test File

```python
# tests/integration/test_templates.py

class TestDraftTemplates:
    """Test draft template functionality"""

    def test_create_template(self, authenticated_client, test_draft):
        """Test creating template from draft"""
        response = authenticated_client.post(
            f'/api/drafts/{test_draft.id}/save-as-template',
            json={'template_name': 'Blog Post Template'}
        )

        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_list_templates(self, authenticated_client, test_user):
        """Test listing user's templates"""
        response = authenticated_client.get('/api/templates')

        assert response.status_code == 200
        assert 'templates' in response.json()

    def test_create_draft_from_template(self, authenticated_client):
        """Test creating new draft from template"""
        # Implementation...
```

### 2. Add Fixtures if Needed

```python
# tests/conftest.py

@pytest.fixture
def test_template(init_database, test_user):
    """Create a test template"""
    template = DraftTemplate(
        name='Test Template',
        content='# Template Content',
        user_id=test_user.id
    )
    db.session.add(template)
    db.session.commit()
    return template
```

### 3. Run Tests

```bash
# Run new tests
pytest tests/integration/test_templates.py -v

# Check coverage
pytest tests/integration/test_templates.py --cov=routes/templates
```

## Benefits of This Testing Architecture

1. **Catch Bugs Early**: Automated tests run on every commit
2. **Refactor Safely**: Change code with confidence tests will catch breaks
3. **Document Behavior**: Tests serve as executable documentation
4. **Faster Development**: Less manual testing, faster feedback
5. **Better Design**: Testable code tends to be better architected

## Resources

- **Test Documentation**: `/tests/README.md`
- **Test Configuration**: `/pytest.ini`
- **CI Pipeline**: `/.github/workflows/tests.yml`
- **Make Commands**: `/Makefile`
- **Example Tests**: `/tests/unit/` and `/tests/integration/`

## Support

For questions about testing:
1. Check existing tests for similar patterns
2. Review `/tests/README.md` for detailed guidance
3. Run `make help` for available commands
4. Consult pytest documentation: https://docs.pytest.org/
