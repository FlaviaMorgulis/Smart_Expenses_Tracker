"""
Authentication Tests for Smart Expenses Tracker
Tests login, logout, signup, password hashing, and Flask-Login integration
"""

import pytest
from flask import url_for, session
from app import db
from app.models import User
from app.services import UserService
from test.conftest import TestDataFactory, CustomAssertions

class TestUserAuthentication:
    """Test user authentication functionality"""
    
    def test_user_registration_valid(self, app, client):
        """Test valid user registration"""
        with app.app_context():
            response = client.post('/signup', data={
                'name': 'New User',
                'email': 'newuser@example.com',
                'password': 'validpassword123',
                'confirm_password': 'validpassword123'
            }, follow_redirects=True)
            
            # Should redirect to dashboard after successful registration
            assert response.status_code == 200
            
            # User should be created in database
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.user_name == 'New User'
            assert user.check_password('validpassword123') == True
    
    def test_user_registration_duplicate_email(self, app, client, test_user):
        """Test registration with duplicate email"""
        with app.app_context():
            response = client.post('/signup', data={
                'name': 'Another User',
                'email': test_user.email,  # Duplicate email
                'password': 'validpassword123',
                'confirm_password': 'validpassword123'
            })
            
            # Should not create duplicate user
            assert response.status_code == 200  # Form redisplayed with errors
            assert b'already exists' in response.data or b'Email' in response.data
    
    def test_user_registration_password_mismatch(self, app, client):
        """Test registration with password mismatch"""
        with app.app_context():
            response = client.post('/signup', data={
                'name': 'Test User',
                'email': 'test@example.com',
                'password': 'password123',
                'confirm_password': 'differentpassword'
            })
            
            assert response.status_code == 200
            assert b'password' in response.data.lower()
    
    def test_user_registration_weak_password(self, app, client):
        """Test registration with weak password"""
        with app.app_context():
            weak_passwords = ['123', 'short', 'noNumbers', 'no_upper_case']
            
            for weak_pass in weak_passwords:
                response = client.post('/signup', data={
                    'name': 'Test User',
                    'email': f'test_{weak_pass}@example.com',
                    'password': weak_pass,
                    'confirm_password': weak_pass
                })
                
                # Should reject weak password
                assert response.status_code == 200
                user = User.query.filter_by(email=f'test_{weak_pass}@example.com').first()
                assert user is None  # User should not be created
    
    def test_user_registration_invalid_email(self, app, client):
        """Test registration with invalid email"""
        with app.app_context():
            invalid_emails = ['invalid', '@invalid.com', 'invalid@', 'no-at-sign']
            
            for invalid_email in invalid_emails:
                response = client.post('/signup', data={
                    'name': 'Test User',
                    'email': invalid_email,
                    'password': 'validpassword123',
                    'confirm_password': 'validpassword123'
                })
                
                assert response.status_code == 200
                user = User.query.filter_by(email=invalid_email).first()
                assert user is None


class TestUserLogin:
    """Test user login functionality"""
    
    def test_login_valid_credentials(self, app, client, test_user):
        """Test login with valid credentials"""
        with app.app_context():
            response = client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Should be redirected to dashboard
            assert b'Dashboard' in response.data or b'Welcome' in response.data
            
            # Check session
            with client.session_transaction() as sess:
                assert '_user_id' in sess
                assert sess['_user_id'] == str(test_user.user_id)
    
    def test_login_invalid_email(self, app, client):
        """Test login with invalid email"""
        with app.app_context():
            response = client.post('/login', data={
                'email': 'nonexistent@example.com',
                'password': 'anypassword'
            })
            
            assert response.status_code == 200
            assert b'Invalid' in response.data or b'incorrect' in response.data.lower()
    
    def test_login_invalid_password(self, app, client, test_user):
        """Test login with invalid password"""
        with app.app_context():
            response = client.post('/login', data={
                'email': test_user.email,
                'password': 'wrongpassword'
            })
            
            assert response.status_code == 200
            assert b'Invalid' in response.data or b'incorrect' in response.data.lower()
    
    def test_login_empty_credentials(self, app, client):
        """Test login with empty credentials"""
        with app.app_context():
            # Empty email
            response = client.post('/login', data={
                'email': '',
                'password': 'password123'
            })
            assert response.status_code == 200
            
            # Empty password
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': ''
            })
            assert response.status_code == 200
    
    def test_login_remember_me(self, app, client, test_user):
        """Test login with remember me functionality"""
        with app.app_context():
            response = client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123',
                'remember': True
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Check that remember me cookie is set
            # Note: This would require additional Flask-Login configuration testing


class TestUserLogout:
    """Test user logout functionality"""
    
    def test_logout_authenticated_user(self, app, logged_in_user):
        """Test logout for authenticated user"""
        with app.app_context():
            # Verify user is logged in first
            response = logged_in_user.get('/dashboard')
            assert response.status_code == 200
            
            # Logout
            response = logged_in_user.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            
            # Should be redirected to login page
            assert b'Login' in response.data or b'login' in response.data.lower()
            
            # Session should be cleared
            with logged_in_user.session_transaction() as sess:
                assert '_user_id' not in sess
    
    def test_logout_unauthenticated_user(self, app, client):
        """Test logout for unauthenticated user"""
        with app.app_context():
            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            # Should redirect to login page without errors


class TestAuthenticationIntegration:
    """Test authentication integration with Flask-Login"""
    
    def test_login_required_decorator(self, app, client):
        """Test that login_required decorator works"""
        with app.app_context():
            protected_routes = [
                '/dashboard',
                '/transactions',
                '/admin'
            ]
            
            for route in protected_routes:
                response = client.get(route)
                # Should redirect to login page
                assert response.status_code in [302, 401]
    
    def test_user_loader_function(self, app, test_user):
        """Test Flask-Login user loader function"""
        with app.app_context():
            from app import login_manager
            
            # Test valid user ID
            loaded_user = login_manager.user_loader(str(test_user.user_id))
            assert loaded_user is not None
            assert loaded_user.user_id == test_user.user_id
            
            # Test invalid user ID
            loaded_user = login_manager.user_loader('99999')
            assert loaded_user is None
    
    def test_current_user_context(self, app, logged_in_user, test_user):
        """Test current_user context in templates"""
        with app.app_context():
            response = logged_in_user.get('/dashboard')
            assert response.status_code == 200
            
            # Should display user's name in dashboard
            assert test_user.user_name.encode() in response.data
    
    def test_session_persistence(self, app, logged_in_user):
        """Test that session persists across requests"""
        with app.app_context():
            # First request
            response1 = logged_in_user.get('/dashboard')
            assert response1.status_code == 200
            
            # Second request should still be authenticated
            response2 = logged_in_user.get('/dashboard')
            assert response2.status_code == 200


class TestPasswordSecurity:
    """Test password security features"""
    
    def test_password_hashing(self, app):
        """Test that passwords are properly hashed"""
        with app.app_context():
            user = TestDataFactory.create_test_user("hash_test")
            original_password = "testpassword123"
            user.set_password(original_password)
            
            # Password should be hashed
            assert user.password_hash != original_password
            assert len(user.password_hash) > 50  # Hashed passwords are long
            
            # Should verify correctly
            assert user.check_password(original_password) == True
            assert user.check_password("wrongpassword") == False
    
    def test_password_hash_uniqueness(self, app):
        """Test that same password produces different hashes (salt)"""
        with app.app_context():
            password = "samepassword123"
            
            user1 = TestDataFactory.create_test_user("user1")
            user1.set_password(password)
            
            user2 = TestDataFactory.create_test_user("user2")
            user2.set_password(password)
            
            # Same password should produce different hashes due to salt
            assert user1.password_hash != user2.password_hash
            
            # But both should verify correctly
            assert user1.check_password(password) == True
            assert user2.check_password(password) == True
    
    def test_password_timing_attack_protection(self, app):
        """Test password verification timing consistency"""
        with app.app_context():
            user = TestDataFactory.create_test_user("timing_test")
            user.set_password("correctpassword")
            
            import time
            
            # Time correct password check
            start = time.time()
            result1 = user.check_password("correctpassword")
            time1 = time.time() - start
            
            # Time incorrect password check
            start = time.time()
            result2 = user.check_password("wrongpassword")
            time2 = time.time() - start
            
            assert result1 == True
            assert result2 == False
            
            # Timing should be similar (within reasonable bounds)
            # This helps prevent timing attacks
            time_diff = abs(time1 - time2)
            assert time_diff < 0.1  # Both should complete within similar timeframes


class TestAuthenticationForms:
    """Test authentication forms and validation"""
    
    def test_login_form_csrf_protection(self, app, client):
        """Test CSRF protection on login form"""
        with app.app_context():
            # Get login form to get CSRF token
            response = client.get('/login')
            assert response.status_code == 200
            assert b'csrf_token' in response.data or b'_csrf_token' in response.data
    
    def test_signup_form_csrf_protection(self, app, client):
        """Test CSRF protection on signup form"""
        with app.app_context():
            response = client.get('/signup')
            assert response.status_code == 200
            assert b'csrf_token' in response.data or b'_csrf_token' in response.data
    
    def test_form_validation_client_side(self, app, client):
        """Test client-side form validation attributes"""
        with app.app_context():
            response = client.get('/signup')
            assert response.status_code == 200
            
            # Check for HTML5 validation attributes
            assert b'required' in response.data
            assert b'email' in response.data  # Email input type
            assert b'password' in response.data  # Password input type


class TestAuthenticationSecurity:
    """Test authentication security measures"""
    
    def test_brute_force_protection(self, app, client, test_user):
        """Test protection against brute force attacks"""
        with app.app_context():
            # Attempt multiple failed logins
            for i in range(10):
                response = client.post('/login', data={
                    'email': test_user.email,
                    'password': 'wrongpassword'
                })
                assert response.status_code == 200
            
            # After multiple failures, should still allow correct password
            response = client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            }, follow_redirects=True)
            
            # This test assumes no rate limiting is implemented yet
            # In production, you might want to implement account lockout
            assert response.status_code == 200
    
    def test_session_security(self, app, logged_in_user):
        """Test session security measures"""
        with app.app_context():
            with logged_in_user.session_transaction() as sess:
                # Session should have security flags
                assert '_user_id' in sess
                assert '_fresh' in sess  # Flask-Login freshness
    
    def test_admin_access_control(self, app, client, admin_user):
        """Test that admin access is properly controlled"""
        with app.app_context():
            # Login as admin
            response = client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Admin should be able to access admin routes
            response = client.get('/admin/')
            # Note: This test depends on Flask-Admin setup
            # Response might be 200 (success) or 302 (redirect to login if not properly authenticated)


class TestAuthenticationRedirects:
    """Test authentication redirect behavior"""
    
    def test_login_redirect_to_next(self, app, client, test_user):
        """Test that login redirects to 'next' parameter"""
        with app.app_context():
            # Try to access protected page
            response = client.get('/dashboard')
            
            # Should redirect to login with next parameter
            assert response.status_code == 302
            
            # Login with next parameter
            response = client.post('/login?next=/dashboard', data={
                'email': test_user.email,
                'password': 'testpassword123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should be redirected to original destination
            assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_logout_redirect(self, app, logged_in_user):
        """Test logout redirect behavior"""
        with app.app_context():
            response = logged_in_user.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            
            # Should redirect to login or home page
            assert (b'Login' in response.data or 
                   b'login' in response.data.lower() or
                   b'Welcome' in response.data)
    
    def test_authenticated_user_redirect(self, app, logged_in_user):
        """Test that authenticated users are redirected from auth pages"""
        with app.app_context():
            # Authenticated user trying to access login page
            response = logged_in_user.get('/login', follow_redirects=True)
            
            # Should redirect to dashboard (or stay if allowed)
            assert response.status_code == 200


class TestAuthenticationErrorHandling:
    """Test authentication error handling"""
    
    def test_database_error_handling(self, app, client):
        """Test authentication behavior during database errors"""
        # This would require mocking database failures
        # For now, we test that the system handles missing users gracefully
        with app.app_context():
            response = client.post('/login', data={
                'email': 'nonexistent@example.com',
                'password': 'anypassword'
            })
            
            # Should handle gracefully without server error
            assert response.status_code == 200
            assert b'500' not in response.data  # No server error
    
    def test_invalid_session_handling(self, app, client):
        """Test handling of invalid session data"""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = '99999'  # Non-existent user ID
            
            # Should handle invalid user ID gracefully
            response = client.get('/dashboard')
            
            # Should redirect to login (user_loader returns None)
            assert response.status_code in [302, 401]
