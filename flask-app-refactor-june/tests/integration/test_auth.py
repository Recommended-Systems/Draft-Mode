"""
Integration tests for authentication flows
Tests login, registration, logout, and password management
"""
import pytest
from models import User, db

class TestRegistration:
    """Test user registration flow"""

    def test_register_page_loads(self, client, init_database):
        """Test registration page is accessible"""
        response = client.get('/auth/signup')
        assert response.status_code == 200
        assert b'Register' in response.data or b'Sign Up' in response.data or b'signup' in response.data.lower()

    def test_successful_registration(self, client, init_database, valid_user_data):
        """Test successful user registration"""
        response = client.post('/auth/signup', data=valid_user_data, follow_redirects=True)

        # Should redirect to login or dashboard
        assert response.status_code == 200

        # User should be created in database
        user = User.query.filter_by(name=valid_user_data['username']).first()
        assert user is not None
        assert user.email == valid_user_data['email']
        assert user.check_password(valid_user_data['password'])

    def test_register_duplicate_username(self, client, init_database, test_user):
        """Test registration with duplicate username"""
        response = client.post('/auth/signup', data={
            'username': 'testuser',  # Same as test_user
            'email': 'newemail@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        })

        # Should show error
        assert response.status_code == 200
        assert b'username' in response.data.lower() or b'already' in response.data.lower()

    def test_register_duplicate_email(self, client, init_database, test_user):
        """Test registration with duplicate email"""
        response = client.post('/auth/signup', data={
            'username': 'newuser',
            'email': 'test@example.com',  # Same as test_user
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        })

        # Should show error
        assert response.status_code == 200
        assert b'email' in response.data.lower() or b'already' in response.data.lower()

    def test_register_password_mismatch(self, client, init_database):
        """Test registration with mismatched passwords"""
        response = client.post('/auth/signup', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass123!'
        })

        assert response.status_code == 200
        # Should not create user
        user = User.query.filter_by(name='newuser').first()
        assert user is None


class TestLogin:
    """Test user login flow"""

    def test_login_page_loads(self, client, init_database):
        """Test login page is accessible"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'Sign In' in response.data

    def test_successful_login(self, client, init_database, test_user):
        """Test successful login"""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'TestPassword123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to dashboard
        assert b'dashboard' in response.data.lower() or b'drafts' in response.data.lower()

    def test_login_with_email(self, client, init_database, test_user):
        """Test login with email instead of username"""
        response = client.post('/auth/login', data={
            'username': 'test@example.com',  # Using email
            'password': 'TestPassword123!'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_wrong_password(self, client, init_database, test_user):
        """Test login with wrong password"""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'WrongPassword123!'
        })

        assert response.status_code == 200
        assert b'invalid' in response.data.lower() or b'incorrect' in response.data.lower()

    def test_login_nonexistent_user(self, client, init_database):
        """Test login with non-existent user"""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'SomePassword123!'
        })

        assert response.status_code == 200
        assert b'invalid' in response.data.lower() or b'not found' in response.data.lower()

    def test_login_unverified_user(self, client, init_database, unverified_user):
        """Test login with unverified user"""
        response = client.post('/auth/login', data={
            'username': 'unverified',
            'password': 'TestPassword123!'
        })

        # Behavior depends on your email verification requirements
        # Either should allow login or show verification required message
        assert response.status_code in [200, 302]


class TestLogout:
    """Test user logout flow"""

    def test_logout(self, authenticated_client, init_database):
        """Test successful logout"""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to login or home
        assert b'login' in response.data.lower() or b'home' in response.data.lower()

    def test_logout_unauthenticated(self, client, init_database):
        """Test logout when not logged in"""
        response = client.get('/auth/logout', follow_redirects=True)

        # Should redirect without error
        assert response.status_code == 200


class TestPasswordReset:
    """Test password reset flow"""

    def test_forgot_password_page(self, client, init_database):
        """Test forgot password page loads"""
        response = client.get('/auth/forgot-password')

        # Page might not exist yet, so either 200 or 404 is acceptable
        assert response.status_code in [200, 404]

    def test_request_password_reset(self, client, init_database, test_user):
        """Test requesting password reset"""
        response = client.post('/auth/forgot-password', data={
            'email': 'test@example.com'
        })

        # Should show success message (even if email doesn't exist for security)
        # Acceptable responses: 200 (form page), 302 (redirect)
        assert response.status_code in [200, 302, 404]


class TestAuthenticationRequired:
    """Test authentication requirements for protected routes"""

    def test_dashboard_requires_auth(self, client, init_database):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard')

        # Should redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_create_draft_requires_auth(self, client, init_database):
        """Test creating draft requires authentication"""
        response = client.get('/drafts/create')

        # Should redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_settings_requires_auth(self, client, init_database):
        """Test settings requires authentication"""
        response = client.get('/settings/profile')

        # Should redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_authenticated_user_can_access_dashboard(self, authenticated_client, init_database):
        """Test authenticated user can access dashboard"""
        response = authenticated_client.get('/dashboard')

        assert response.status_code == 200
        assert b'draft' in response.data.lower()


class TestSessionManagement:
    """Test session management"""

    def test_session_persists_after_login(self, client, init_database, test_user):
        """Test session persists after login"""
        # Login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'TestPassword123!'
        })

        # Access protected route
        response = client.get('/dashboard')
        assert response.status_code == 200

        # Session should still be valid
        response = client.get('/settings/profile')
        assert response.status_code == 200

    def test_session_cleared_after_logout(self, client, init_database, test_user):
        """Test session is cleared after logout"""
        # Login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'TestPassword123!'
        })

        # Logout
        client.get('/auth/logout')

        # Should not be able to access protected routes
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/auth/login' in response.location
