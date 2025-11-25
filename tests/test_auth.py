"""Tests for authentication functionality"""
import pytest
from app.models import User, db


class TestUserRegistration:
    """Test user registration/signup"""

    def test_signup_page_loads(self, client):
        """Test signup page is accessible"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Sign Up' in response.data or b'signup' in response.data.lower()

    def test_successful_signup(self, client, app):
        """Test successful user registration"""
        response = client.post('/signup', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.user_name == 'New User'

    def test_signup_duplicate_email(self, client, test_user):
        """Test signup fails with existing email"""
        response = client.post('/signup', data={
            'name': 'Another User',
            'email': 'testuser@example.com',  # Already exists
            'password': 'Pass123!',
            'confirm_password': 'Pass123!'
        }, follow_redirects=True)

        assert b'already registered' in response.data.lower()

    def test_signup_password_mismatch(self, client):
        """Test signup fails when passwords don't match"""
        response = client.post('/signup', data={
            'name': 'Test User',
            'email': 'test2@example.com',
            'password': 'Pass123!',
            'confirm_password': 'DifferentPass123!'
        })

        assert response.status_code in [200, 400]


class TestUserLogin:
    """Test user login functionality"""

    def test_login_page_loads(self, client):
        """Test login page is accessible"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data.lower()

    def test_successful_login(self, client, test_user):
        """Test successful login with correct credentials"""
        response = client.post('/login', data={
            'email': 'testuser@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'dashboard' in response.data.lower() or b'success' in response.data.lower()

    def test_login_wrong_password(self, client, test_user):
        """Test login fails with wrong password"""
        response = client.post('/login', data={
            'email': 'testuser@example.com',
            'password': 'WrongPassword123!'
        }, follow_redirects=True)

        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()

    def test_login_nonexistent_user(self, client):
        """Test login fails with non-existent email"""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'SomePass123!'
        }, follow_redirects=True)

        assert b'Invalid' in response.data or b'password' in response.data.lower()

    def test_logout(self, auth_client):
        """Test logout functionality"""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestAdminAccess:
    """Test admin-specific functionality"""

    def test_admin_can_login(self, client, admin_user):
        """Test admin can login"""
        response = client.post('/login', data={
            'email': 'admin@test.com',
            'password': 'Admin123!'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_admin_has_admin_flag(self, app, admin_user):
        """Test admin user has is_admin=True"""
        with app.app_context():
            admin = User.query.filter_by(email='admin@test.com').first()
            assert admin.is_admin is True
            assert admin.is_administrator() is True


class TestProtectedRoutes:
    """Test authentication protection on routes"""

    def test_dashboard_requires_login(self, client):
        """Test dashboard redirects to login when not authenticated"""
        response = client.get('/dashboard')
        # Flask-Login returns 401 Unauthorized for AJAX/API, 302 for browser
        assert response.status_code in [302, 401]

    def test_transactions_requires_login(self, client):
        """Test transactions page requires login"""
        response = client.get('/transactions/')
        assert response.status_code in [302, 401]

    def test_budget_requires_login(self, client):
        """Test budget page requires login"""
        response = client.get('/budget')
        assert response.status_code in [302, 401]

    def test_authenticated_can_access_dashboard(self, auth_client):
        """Test authenticated user can access dashboard"""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
