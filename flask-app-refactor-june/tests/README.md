# Testing Documentation for Draft Mode

## Overview

This testing suite provides comprehensive coverage for the Draft Mode application, ensuring reliability, security, and maintainability as new features are added.

## Testing Architecture

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── test_models.py      # Database model tests
│   └── test_encryption.py  # Encryption utility tests
├── integration/             # Integration tests for workflows
│   ├── test_auth.py        # Authentication flow tests
│   ├── test_drafts.py      # Draft management tests
│   └── test_publishing.py  # Publishing feature tests
└── fixtures/                # Test data and mock objects
```

### Test Categories

#### 1. Unit Tests
- **Models**: Test database models, relationships, and validation
- **Utilities**: Test encryption, security logging, email services
- **Helpers**: Test standalone functions and utilities

#### 2. Integration Tests
- **Authentication**: Login, registration, logout, password reset
- **Draft Management**: Creating, editing, deleting drafts and versions
- **Publishing**: Ghost API integration, platform configuration
- **API Endpoints**: REST API functionality
- **Settings**: User preferences and configuration

#### 3. End-to-End Tests (Future)
- Full user workflows
- Multi-user collaboration scenarios
- Performance benchmarks

## Running Tests

### Install Testing Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_models.py

# Specific test class
pytest tests/unit/test_models.py::TestUserModel

# Specific test function
pytest tests/unit/test_models.py::TestUserModel::test_create_user
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Tests in Parallel

```bash
# Run tests in parallel (faster for large test suites)
pytest -n auto
```

### Run Tests with Verbose Output

```bash
pytest -v -s
```

## Writing Tests

### Test Structure Pattern

```python
class TestFeatureName:
    """Test feature description"""

    def test_specific_behavior(self, fixture1, fixture2):
        """Test what this specific test validates"""
        # Arrange: Set up test data
        user = User(username='test', email='test@example.com')

        # Act: Execute the code being tested
        user.set_password('password123')

        # Assert: Verify expected behavior
        assert user.check_password('password123') is True
```

### Using Fixtures

Fixtures are defined in `conftest.py` and provide reusable test data:

```python
def test_with_user(test_user):
    """Test using the test_user fixture"""
    assert test_user.username == 'testuser'
    assert test_user.is_verified is True
```

Available fixtures:
- `app`: Flask application instance
- `client`: Test client for making requests
- `init_database`: Fresh database for each test
- `test_user`: Pre-created user account
- `authenticated_client`: Client with active session
- `test_draft`: Sample draft with version
- `ghost_platform`: Configured Ghost platform

### Mocking External Services

Use `unittest.mock` to mock external API calls:

```python
from unittest.mock import patch, MagicMock

@patch('routes.publish.requests.post')
def test_ghost_api(mock_post, authenticated_client, test_draft):
    """Test Ghost API integration"""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'posts': [{'id': '123'}]}
    mock_post.return_value = mock_response

    # Test the functionality
    response = authenticated_client.post('/api/publish/ghost/1')
    assert response.status_code == 200
```

## Coverage Goals

### Minimum Coverage Requirements

- **Overall Code Coverage**: 70%
- **Critical Paths**: 100%
  - Authentication flows
  - Data encryption/decryption
  - Payment processing (if applicable)
  - Security features

### Coverage by Module

| Module | Target Coverage | Critical |
|--------|----------------|----------|
| models.py | 90% | Yes |
| routes/auth.py | 95% | Yes |
| routes/drafts.py | 85% | No |
| routes/publish.py | 80% | No |
| utils/encryption.py | 100% | Yes |
| utils/security_logger.py | 90% | Yes |

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures to set up clean state
- Don't rely on test execution order

### 2. Test Naming
```python
# Good: Descriptive test names
def test_user_cannot_login_with_wrong_password():
    pass

# Bad: Generic test names
def test_login():
    pass
```

### 3. Assertions
```python
# Good: Specific assertions
assert user.username == 'testuser'
assert len(drafts) == 3
assert response.status_code == 200

# Bad: Vague assertions
assert user
assert drafts
assert response
```

### 4. Test Data
```python
# Good: Use meaningful test data
email = 'john.doe@example.com'
password = 'SecurePassword123!'

# Bad: Use unclear test data
email = 'test@test.com'
password = 'password'
```

### 5. Error Testing
Always test both success and failure cases:

```python
def test_create_user_success(self, client):
    """Test successful user creation"""
    # Test success case

def test_create_user_duplicate_email(self, client):
    """Test user creation with duplicate email fails"""
    # Test failure case
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Security Testing

### Run Security Audit

```bash
# Check for known vulnerabilities
safety check

# Security linting
bandit -r . -x ./tests,./venv
```

### Common Security Test Patterns

1. **SQL Injection**: Test with malicious input
2. **XSS**: Test script injection in user input
3. **CSRF**: Verify CSRF token validation
4. **Authentication**: Test unauthorized access
5. **Encryption**: Verify sensitive data is encrypted

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class DraftModeUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def view_dashboard(self):
        self.client.get("/dashboard")

    @task(3)
    def create_draft(self):
        self.client.post("/drafts/create", {
            "title": "Test Draft",
            "description": "Test"
        })
```

Run load tests:
```bash
locust -f locustfile.py --host=http://localhost:5000
```

## Debugging Tests

### Run Tests with PDB

```bash
pytest --pdb  # Drop into debugger on failure
```

### Print Debugging

```bash
pytest -s  # Show print statements
```

### Verbose Output

```bash
pytest -vv  # Extra verbose output
```

## Troubleshooting

### Common Issues

**Issue**: Database persistence between tests
```python
# Solution: Use init_database fixture
def test_something(init_database):
    # Database is fresh for this test
```

**Issue**: Authentication not working in tests
```python
# Solution: Use authenticated_client fixture
def test_protected_route(authenticated_client):
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
```

**Issue**: External API calls failing tests
```python
# Solution: Mock the external calls
@patch('module.requests.post')
def test_api(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
```

## Future Testing Enhancements

1. **Visual Regression Testing**: Screenshot comparison for UI changes
2. **Accessibility Testing**: WCAG compliance validation
3. **Cross-browser Testing**: Selenium/Playwright tests
4. **API Contract Testing**: Ensure API compatibility
5. **Mutation Testing**: Test the quality of tests themselves

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing Guide](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Testing Best Practices](https://testdriven.io/blog/modern-flask/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

## Contact

For questions about testing:
- Review existing tests in the `tests/` directory
- Check test patterns in `conftest.py`
- Consult this README for testing guidelines
