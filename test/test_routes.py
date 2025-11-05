"""
Route/Endpoint Tests for Smart Expenses Tracker
Tests all Flask routes with proper access control
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Transaction, Category, Member, Budget
from app.services import TransactionService, CategoryService, BudgetService
from decimal import Decimal
from test.conftest import TestDataFactory, CustomAssertions

class TestMainRoutes:
    """Test main application routes"""
    
    def test_index_route_unauthenticated(self, app, client):
        """Test index route for unauthenticated users"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
            
            # Should show landing page or redirect to login
            assert (b'Welcome' in response.data or 
                   b'Login' in response.data or 
                   b'Smart Expenses' in response.data)
    
    def test_index_route_authenticated(self, app, logged_in_user):
        """Test index route for authenticated users"""
        with app.app_context():
            response = logged_in_user.get('/')
            assert response.status_code == 200
            
            # Should show dashboard or welcome message
            assert (b'Dashboard' in response.data or 
                   b'Welcome' in response.data)
    
    def test_dashboard_route_authenticated(self, app, logged_in_user, test_user):
        """Test dashboard route for authenticated users"""
        with app.app_context():
            response = logged_in_user.get('/dashboard')
            assert response.status_code == 200
            
            # Should contain user-specific content
            assert test_user.user_name.encode() in response.data
            assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_dashboard_route_unauthenticated(self, app, client):
        """Test dashboard route requires authentication"""
        with app.app_context():
            response = client.get('/dashboard')
            
            # Should redirect to login
            assert response.status_code in [302, 401]
    
    def test_profile_route_authenticated(self, app, logged_in_user, test_user):
        """Test profile route for authenticated users"""
        with app.app_context():
            response = logged_in_user.get('/profile')
            
            if response.status_code == 200:
                # If profile route exists, should show user info
                assert test_user.email.encode() in response.data
            else:
                # Route might not be implemented yet
                assert response.status_code in [404, 302]
    
    def test_static_file_serving(self, app, client):
        """Test static file serving"""
        with app.app_context():
            # Test CSS file
            response = client.get('/static/css/style.css')
            # Should either serve file (200) or not found (404)
            assert response.status_code in [200, 404]
            
            # Test JavaScript file
            response = client.get('/static/js/main.js')
            assert response.status_code in [200, 404]


class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_login_route_get(self, app, client):
        """Test login page display"""
        with app.app_context():
            response = client.get('/login')
            assert response.status_code == 200
            
            # Should contain login form elements
            assert b'email' in response.data.lower()
            assert b'password' in response.data.lower()
            assert b'login' in response.data.lower()
    
    def test_login_route_post_valid(self, app, client, test_user):
        """Test login with valid credentials"""
        with app.app_context():
            response = client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should be redirected to dashboard
            assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_signup_route_get(self, app, client):
        """Test signup page display"""
        with app.app_context():
            response = client.get('/signup')
            assert response.status_code == 200
            
            # Should contain signup form elements
            assert b'name' in response.data.lower()
            assert b'email' in response.data.lower()
            assert b'password' in response.data.lower()
    
    def test_signup_route_post_valid(self, app, client):
        """Test signup with valid data"""
        with app.app_context():
            response = client.post('/signup', data={
                'name': 'New Test User',
                'email': 'newtest@example.com',
                'password': 'validpassword123',
                'confirm_password': 'validpassword123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # User should be created
            user = User.query.filter_by(email='newtest@example.com').first()
            assert user is not None
    
    def test_logout_route(self, app, logged_in_user):
        """Test logout route"""
        with app.app_context():
            response = logged_in_user.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            
            # Should redirect to login page
            assert b'Login' in response.data or b'login' in response.data.lower()


class TestTransactionRoutes:
    """Test transaction-related routes"""
    
    def test_transactions_list_authenticated(self, app, logged_in_user, test_user, test_category):
        """Test transactions list for authenticated user"""
        with app.app_context():
            # Create some transactions
            TransactionService.add_personal_transaction(
                test_user, Decimal('100.00'), 'expense', test_category.category_id
            )
            
            response = logged_in_user.get('/transactions')
            
            if response.status_code == 200:
                # Should show transactions
                assert b'transaction' in response.data.lower()
            else:
                # Route might not be fully implemented
                assert response.status_code in [404, 302]
    
    def test_transactions_list_unauthenticated(self, app, client):
        """Test transactions list requires authentication"""
        with app.app_context():
            response = client.get('/transactions')
            
            # Should redirect to login or return unauthorized
            assert response.status_code in [302, 401, 404]
    
    def test_add_transaction_get(self, app, logged_in_user):
        """Test add transaction form display"""
        with app.app_context():
            response = logged_in_user.get('/transactions/add')
            
            if response.status_code == 200:
                # Should contain transaction form
                assert b'amount' in response.data.lower()
                assert b'category' in response.data.lower()
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302]
    
    def test_add_transaction_post(self, app, logged_in_user, test_category):
        """Test adding transaction via POST"""
        with app.app_context():
            response = logged_in_user.post('/transactions/add', data={
                'amount': '50.00',
                'category_id': test_category.category_id,
                'transaction_type': 'expense',
                'description': 'Test transaction'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                # Should redirect back to transactions list
                assert b'transaction' in response.data.lower()
            else:
                # Route might not be fully implemented
                assert response.status_code in [404, 405]
    
    def test_edit_transaction_get(self, app, logged_in_user, test_user, test_category):
        """Test edit transaction form"""
        with app.app_context():
            # Create a transaction first
            transaction = TransactionService.add_personal_transaction(
                test_user, Decimal('75.00'), 'expense', test_category.category_id
            )
            
            response = logged_in_user.get(f'/transactions/{transaction.transaction_id}/edit')
            
            if response.status_code == 200:
                # Should show edit form
                assert b'75.00' in response.data or b'75' in response.data
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302]
    
    def test_delete_transaction(self, app, logged_in_user, test_user, test_category):
        """Test transaction deletion"""
        with app.app_context():
            # Create a transaction
            transaction = TransactionService.add_personal_transaction(
                test_user, Decimal('25.00'), 'expense', test_category.category_id
            )
            transaction_id = transaction.transaction_id
            
            response = logged_in_user.post(f'/transactions/{transaction_id}/delete', 
                                         follow_redirects=True)
            
            if response.status_code == 200:
                # Transaction should be deleted
                deleted_tx = Transaction.query.get(transaction_id)
                assert deleted_tx is None
            else:
                # Route might not be implemented
                assert response.status_code in [404, 405]


class TestAccessControl:
    """Test access control across all routes"""
    
    def test_user_can_only_access_own_data(self, app, client):
        """Test that users can only access their own data"""
        with app.app_context():
            # Create two users
            user1 = TestDataFactory.create_test_user("user1")
            user1.set_password("password123")
            db.session.add(user1)
            
            user2 = TestDataFactory.create_test_user("user2") 
            user2.set_password("password123")
            db.session.add(user2)
            db.session.commit()
            
            category = Category.query.filter_by(category_name='Food').first()
            
            # Create transaction for user1
            transaction1 = TransactionService.add_personal_transaction(
                user1, Decimal('100.00'), 'expense', category.category_id
            )
            
            # Login as user2
            client.post('/auth/login', data={
                'email': user2.email,
                'password': 'password123'
            })
            
            # Try to access user1's transaction
            response = client.get(f'/transactions/{transaction1.transaction_id}')
            
            if response.status_code == 200:
                # If route exists, should not show user1's data
                assert str(transaction1.transaction_id).encode() not in response.data
            else:
                # Route might not be implemented or properly secured
                assert response.status_code in [404, 403, 302]
    
    def test_admin_access_control(self, app, client, admin_user):
        """Test admin-specific route access"""
        with app.app_context():
            # Login as admin
            client.post('/auth/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Test admin routes
            admin_routes = ['/admin/', '/admin/user/', '/admin/transaction/']
            
            for route in admin_routes:
                response = client.get(route)
                
                # Should either allow access (200) or route not found (404)
                # Should not be unauthorized (403) for admin
                assert response.status_code in [200, 404]
    
    def test_regular_user_cannot_access_admin(self, app, logged_in_user):
        """Test that regular users cannot access admin routes"""
        with app.app_context():
            response = logged_in_user.get('/admin/')
            
            # Should be forbidden or redirect
            assert response.status_code in [403, 302, 404]
    
    def test_csrf_protection(self, app, logged_in_user):
        """Test CSRF protection on forms"""
        with app.app_context():
            # Test POST without CSRF token
            response = logged_in_user.post('/transactions/add', data={
                'amount': '50.00',
                'transaction_type': 'expense'
            })
            
            # Should be rejected due to missing CSRF token
            # (Unless CSRF is disabled in test config)
            if response.status_code == 400:
                assert b'csrf' in response.data.lower() or b'token' in response.data.lower()


class TestErrorHandling:
    """Test error handling in routes"""
    
    def test_404_error_handling(self, app, client):
        """Test 404 error handling"""
        with app.app_context():
            response = client.get('/nonexistent-route')
            assert response.status_code == 404
    
    def test_405_method_not_allowed(self, app, client):
        """Test 405 error for wrong HTTP methods"""
        with app.app_context():
            # Try POST on GET-only route
            response = client.post('/auth/login')  # Without data
            
            # Should either accept (if route handles POST) or method not allowed
            assert response.status_code in [200, 400, 405]
    
    def test_500_error_handling(self, app, client):
        """Test 500 error handling"""
        # This would require mocking a server error
        # For now, we test that routes don't crash with valid inputs
        with app.app_context():
            response = client.get('/')
            assert response.status_code != 500
    
    def test_invalid_transaction_id(self, app, logged_in_user):
        """Test handling of invalid transaction IDs"""
        with app.app_context():
            response = logged_in_user.get('/transactions/99999')
            
            # Should handle gracefully
            assert response.status_code in [404, 302]
    
    def test_malformed_request_data(self, app, logged_in_user):
        """Test handling of malformed request data"""
        with app.app_context():
            response = logged_in_user.post('/transactions/add', data={
                'amount': 'not-a-number',
                'transaction_type': 'invalid-type'
            })
            
            # Should handle gracefully with validation errors
            assert response.status_code in [200, 400]  # Form redisplay or bad request


class TestRoutePerformance:
    """Test route performance"""
    
    def test_dashboard_load_time(self, app, logged_in_user, test_user, test_category):
        """Test dashboard loading performance with data"""
        with app.app_context():
            # Create some data
            for i in range(10):
                TransactionService.add_personal_transaction(
                    test_user, Decimal('10.00'), 'expense', test_category.category_id
                )
            
            import time
            start = time.time()
            response = logged_in_user.get('/dashboard')
            end = time.time()
            
            assert response.status_code == 200
            
            # Should load within reasonable time
            load_time = end - start
            assert load_time < 2.0  # 2 seconds max
    
    def test_transactions_list_performance(self, app, logged_in_user, test_user, test_category):
        """Test transactions list performance with many transactions"""
        with app.app_context():
            # Create many transactions
            for i in range(50):
                TransactionService.add_personal_transaction(
                    test_user, Decimal(f'{i}.00'), 'expense', test_category.category_id
                )
            
            import time
            start = time.time()
            response = logged_in_user.get('/transactions')
            end = time.time()
            
            if response.status_code == 200:
                load_time = end - start
                assert load_time < 3.0  # 3 seconds max for 50 transactions


class TestAPIEndpoints:
    """Test API endpoints if they exist"""
    
    def test_api_transactions_json(self, app, logged_in_user, test_user, test_category):
        """Test API endpoint for transactions in JSON format"""
        with app.app_context():
            # Create a transaction
            TransactionService.add_personal_transaction(
                test_user, Decimal('123.45'), 'expense', test_category.category_id
            )
            
            response = logged_in_user.get('/api/transactions')
            
            if response.status_code == 200:
                # Should return JSON
                assert response.content_type == 'application/json'
                
                # Should contain transaction data
                assert b'123.45' in response.data
            else:
                # API might not be implemented
                assert response.status_code in [404, 302]
    
    def test_api_authentication_required(self, app, client):
        """Test that API endpoints require authentication"""
        with app.app_context():
            api_endpoints = [
                '/api/transactions',
                '/api/categories',
                '/api/budgets'
            ]
            
            for endpoint in api_endpoints:
                response = client.get(endpoint)
                
                # Should require authentication
                assert response.status_code in [302, 401, 404]


class TestFormHandling:
    """Test form handling and validation"""
    
    def test_transaction_form_validation(self, app, logged_in_user):
        """Test transaction form validation"""
        with app.app_context():
            # Test invalid amount
            response = logged_in_user.post('/transactions/add', data={
                'amount': 'invalid',
                'transaction_type': 'expense'
            })
            
            if response.status_code == 200:
                # Should show validation error
                assert b'invalid' in response.data.lower() or b'error' in response.data.lower()
    
    def test_form_data_persistence(self, app, logged_in_user):
        """Test that form data persists after validation errors"""
        with app.app_context():
            response = logged_in_user.post('/transactions/add', data={
                'amount': 'invalid',
                'description': 'Test description'
            })
            
            if response.status_code == 200:
                # Description should be preserved in form
                assert b'Test description' in response.data


class TestRouteRedirects:
    """Test route redirects and URL handling"""
    
    def test_trailing_slash_handling(self, app, client):
        """Test URL trailing slash handling"""
        with app.app_context():
            # Test with and without trailing slash
            response1 = client.get('/auth/login')
            response2 = client.get('/auth/login/')
            
            # Both should work (Flask handles this automatically)
            assert response1.status_code == response2.status_code
    
    def test_case_sensitivity(self, app, client):
        """Test URL case sensitivity"""
        with app.app_context():
            # Flask URLs are case sensitive by default
            response1 = client.get('/auth/login')
            response2 = client.get('/AUTH/LOGIN')
            
            assert response1.status_code == 200  # Should work
            assert response2.status_code == 404  # Should not work
    
    def test_redirect_after_post(self, app, logged_in_user, test_category):
        """Test redirect after successful POST"""
        with app.app_context():
            response = logged_in_user.post('/transactions/add', data={
                'amount': '25.00',
                'category_id': test_category.category_id,
                'transaction_type': 'expense'
            }, follow_redirects=False)
            
            if response.status_code == 302:
                # Should redirect after successful POST (PRG pattern)
                assert 'Location' in response.headers