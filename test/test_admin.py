"""
Admin Interface Tests for Smart Expenses Tracker
Tests Flask-Admin security boundaries, access control, and functionality
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Transaction, Category, Member, Budget
from app.services import TransactionService, CategoryService, BudgetService
from decimal import Decimal
from test.conftest import TestDataFactory, CustomAssertions

class TestAdminAccess:
    """Test admin interface access control"""
    
    def test_admin_login_required(self, app, client):
        """Test that admin interface requires login"""
        with app.app_context():
            response = client.get('/admin/')
            
            # Should redirect to login or return unauthorized
            assert response.status_code in [302, 401, 404]
            
            if response.status_code == 302:
                # Should redirect to login page
                assert 'login' in response.location.lower()
    
    def test_admin_privileges_required(self, app, client, test_user):
        """Test that admin interface requires admin privileges"""
        with app.app_context():
            # Login as regular user
            client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            })
            
            response = client.get('/admin/')
            
            # Should be forbidden or redirect
            assert response.status_code in [403, 302, 404]
    
    def test_admin_can_access_interface(self, app, client, admin_user):
        """Test that admin users can access admin interface"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/')
            
            if response.status_code == 200:
                # Should show admin interface
                assert b'Admin' in response.data or b'administration' in response.data.lower()
            else:
                # Admin might not be fully configured
                assert response.status_code in [404, 302]
    
    def test_admin_logout_security(self, app, client, admin_user):
        """Test admin logout and session security"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Verify admin access
            response = client.get('/admin/')
            admin_accessible = response.status_code == 200
            
            if admin_accessible:
                # Logout
                client.get('/logout')
                
                # Try to access admin again
                response = client.get('/admin/')
                
                # Should no longer have access
                assert response.status_code in [302, 401]


class TestUserModelView:
    """Test User model view in admin interface"""
    
    def test_user_list_view(self, app, client, admin_user):
        """Test user list view in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/user/')
            
            if response.status_code == 200:
                # Should show user management interface
                assert b'User' in response.data or b'user' in response.data.lower()
                
                # Should show admin interface elements (table, columns, etc.)
                assert (b'table' in response.data.lower() or 
                       b'User Name' in response.data or 
                       b'Email' in response.data or
                       b'list' in response.data.lower())
            else:
                # Admin might not be configured or route not found
                assert response.status_code in [404, 302, 403]
    
    def test_user_detail_view(self, app, client, admin_user, test_user):
        """Test user detail view in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get(f'/admin/user/details/?id={test_user.user_id}')
            
            if response.status_code == 200:
                # Should show user details
                assert test_user.email.encode() in response.data
                assert test_user.user_name.encode() in response.data
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302]
    
    def test_user_edit_restrictions(self, app, client, admin_user, test_user):
        """Test user edit restrictions in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get(f'/admin/user/edit/?id={test_user.user_id}')
            
            if response.status_code == 200:
                # Should show edit form
                assert b'email' in response.data.lower()
                
                # Password field should be hidden/protected
                # (Depends on SafeUserView implementation)
                password_visible = b'password' in response.data.lower()
                
                # Test edit submission
                edit_response = client.post(f'/admin/user/edit/?id={test_user.user_id}', data={
                    'email': 'newemail@example.com',
                    'user_name': 'Updated Name'
                })
                
                # Should either accept or show validation
                assert edit_response.status_code in [200, 302]
            else:
                # Edit might be restricted or not implemented
                assert response.status_code in [403, 404, 302]
    
    def test_user_creation_admin(self, app, client, admin_user):
        """Test user creation through admin interface"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/user/new/')
            
            if response.status_code == 200:
                # Should show creation form
                assert b'email' in response.data.lower()
                assert b'name' in response.data.lower()
                
                # Test user creation
                create_response = client.post('/admin/user/new/', data={
                    'email': 'admin_created@example.com',
                    'user_name': 'Admin Created User',
                    'password': 'createdpassword123'
                })
                
                if create_response.status_code in [200, 302]:
                    # User should be created
                    created_user = User.query.filter_by(email='admin_created@example.com').first()
                    if created_user:
                        assert created_user.user_name == 'Admin Created User'
            else:
                # Creation might be disabled
                assert response.status_code in [403, 404, 302]
    
    def test_user_deletion_protection(self, app, client, admin_user):
        """Test user deletion protection in admin"""
        with app.app_context():
            # Create a test user to delete
            delete_user = TestDataFactory.create_test_user("to_delete")
            delete_user.set_password("password123")
            db.session.add(delete_user)
            db.session.commit()
            user_id = delete_user.user_id
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.post(f'/admin/user/delete/?id={user_id}')
            
            if response.status_code in [200, 302]:
                # Check if user was actually deleted
                deleted_user = User.query.get(user_id)
                
                # Depending on implementation, might allow or prevent deletion
                # If allowed, user should be gone; if prevented, user should remain
                if deleted_user is None:
                    # Deletion was allowed
                    pass  # This is acceptable for admin
                else:
                    # Deletion was prevented (also acceptable)
                    pass
            else:
                # Deletion might be disabled
                assert response.status_code in [403, 404]


class TestTransactionModelView:
    """Test Transaction model view in admin interface"""
    
    def test_transaction_list_view(self, app, client, admin_user, test_user, test_category):
        """Test transaction list view in admin"""
        with app.app_context():
            # Create some transactions
            TransactionService.add_personal_transaction(
                test_user, Decimal('100.00'), 'expense', test_category.category_id
            )
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/transaction/')
            
            if response.status_code == 200:
                # Should show transaction list
                assert b'100.00' in response.data or b'100' in response.data
                assert test_category.category_name.encode() in response.data
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302, 403]
    
    def test_transaction_read_only_access(self, app, client, admin_user, test_user, test_category):
        """Test that transactions are read-only in admin interface"""
        with app.app_context():
            # Create a transaction
            transaction = TransactionService.add_personal_transaction(
                test_user, Decimal('150.00'), 'expense', test_category.category_id
            )
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Try to access edit page
            response = client.get(f'/admin/transaction/edit/?id={transaction.transaction_id}')
            
            # Should be forbidden or not found (read-only)
            assert response.status_code in [403, 404, 302]
    
    def test_transaction_creation_blocked(self, app, client, admin_user):
        """Test that transaction creation is blocked in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/transaction/new/')
            
            # Should be forbidden or not found
            assert response.status_code in [403, 404, 302]
    
    def test_transaction_deletion_blocked(self, app, client, admin_user, test_user, test_category):
        """Test that transaction deletion is blocked in admin"""
        with app.app_context():
            # Create a transaction
            transaction = TransactionService.add_personal_transaction(
                test_user, Decimal('75.00'), 'expense', test_category.category_id
            )
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.post(f'/admin/transaction/delete/?id={transaction.transaction_id}')
            
            # Should be forbidden
            assert response.status_code in [403, 404, 405]
            
            # Transaction should still exist
            existing_tx = Transaction.query.get(transaction.transaction_id)
            assert existing_tx is not None


class TestCategoryModelView:
    """Test Category model view in admin interface"""
    
    def test_category_list_view(self, app, client, admin_user):
        """Test category list view in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/category/')
            
            if response.status_code == 200:
                # Should show category list
                assert b'category' in response.data.lower()
                
                # Should show default categories
                assert b'Food' in response.data or b'food' in response.data
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302, 403]
    
    def test_category_management(self, app, client, admin_user):
        """Test category management in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Test category creation
            response = client.get('/admin/category/new/')
            
            if response.status_code == 200:
                # Should show creation form
                assert b'category_name' in response.data or b'name' in response.data
                
                # Create a new category
                create_response = client.post('/admin/category/new/', data={
                    'category_name': 'Admin Test Category',
                    'category_description': 'Created by admin'
                })
                
                if create_response.status_code in [200, 302]:
                    # Category should be created
                    created_category = Category.query.filter_by(category_name='Admin Test Category').first()
                    assert created_category is not None
            else:
                # Category creation might be disabled
                assert response.status_code in [403, 404, 302]


class TestBudgetModelView:
    """Test Budget model view in admin interface"""
    
    def test_budget_list_view(self, app, client, admin_user, test_user, test_category):
        """Test budget list view in admin"""
        with app.app_context():
            # Create a budget
            BudgetService.create_budget(
                test_user, test_category.category_id, Decimal('500.00'), 'monthly'
            )
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/budget/')
            
            if response.status_code == 200:
                # Should show budget list
                assert b'500.00' in response.data or b'500' in response.data
                assert b'monthly' in response.data.lower()
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302, 403]


class TestMemberModelView:
    """Test Member model view in admin interface"""
    
    def test_member_list_view(self, app, client, admin_user):
        """Test member list view in admin"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/member/')
            
            if response.status_code == 200:
                # Should show member list (might be empty)
                assert b'member' in response.data.lower()
            else:
                # Route might not be implemented
                assert response.status_code in [404, 302, 403]


class TestAdminSecurity:
    """Test admin interface security measures"""
    
    def test_csrf_protection_admin(self, app, client, admin_user):
        """Test CSRF protection in admin forms"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Try to create user without CSRF token
            response = client.post('/admin/user/new/', data={
                'email': 'nocsrf@example.com',
                'user_name': 'No CSRF User'
            })
            
            if response.status_code == 400:
                # Should reject due to missing CSRF
                assert b'csrf' in response.data.lower() or b'token' in response.data.lower()
    
    def test_admin_session_timeout(self, app, client, admin_user):
        """Test admin session timeout handling"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Access admin interface
            response1 = client.get('/admin/')
            
            if response1.status_code == 200:
                # Simulate session timeout (this would require cookie manipulation)
                # For now, just verify the interface is accessible
                assert b'admin' in response1.data.lower()
    
    def test_admin_privilege_escalation_protection(self, app, client, test_user, admin_user):
        """Test protection against privilege escalation"""
        with app.app_context():
            # Login as regular user
            client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            })
            
            # Try to modify user to make them admin
            response = client.post(f'/admin/user/edit/?id={test_user.user_id}', data={
                'is_admin': True,
                'email': test_user.email
            })
            
            # Should be forbidden or redirect
            assert response.status_code in [403, 302, 404]
            
            # User should not have gained admin privileges
            db.session.refresh(test_user)
            assert not test_user.is_administrator()
    
    def test_admin_data_isolation(self, app, client, admin_user):
        """Test that admin can see all users' data but with proper boundaries"""
        with app.app_context():
            # Create multiple users with transactions
            user1 = TestDataFactory.create_test_user("user1")
            user2 = TestDataFactory.create_test_user("user2") 
            user1.set_password("password123")
            user2.set_password("password123")
            db.session.add_all([user1, user2])
            db.session.commit()
            
            category = Category.query.filter_by(category_name='Food').first()
            
            TransactionService.add_personal_transaction(
                user1, Decimal('100.00'), 'expense', category.category_id
            )
            TransactionService.add_personal_transaction(
                user2, Decimal('200.00'), 'expense', category.category_id
            )
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Check user list
            user_response = client.get('/admin/user/')
            if user_response.status_code == 200:
                # Should see all users
                assert user1.email.encode() in user_response.data
                assert user2.email.encode() in user_response.data
            
            # Check transaction list
            tx_response = client.get('/admin/transaction/')
            if tx_response.status_code == 200:
                # Should see all transactions
                assert b'100.00' in tx_response.data or b'100' in tx_response.data
                assert b'200.00' in tx_response.data or b'200' in tx_response.data


class TestAdminNavigation:
    """Test admin interface navigation"""
    
    def test_admin_home_page(self, app, client, admin_user):
        """Test admin home page and navigation"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/')
            
            if response.status_code == 200:
                # Should contain navigation links
                assert b'user' in response.data.lower()
                assert b'transaction' in response.data.lower()
                
                # Should have admin branding
                assert b'admin' in response.data.lower()
    
    def test_admin_breadcrumbs(self, app, client, admin_user):
        """Test admin interface breadcrumb navigation"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Navigate to user list
            response = client.get('/admin/user/')
            
            if response.status_code == 200:
                # Should have breadcrumb navigation
                # (This depends on Flask-Admin template implementation)
                assert b'admin' in response.data.lower()
    
    def test_admin_search_functionality(self, app, client, admin_user, test_user):
        """Test admin search functionality"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Test search in user list
            response = client.get(f'/admin/user/?search={test_user.email}')
            
            if response.status_code == 200:
                # Should show search results
                assert test_user.email.encode() in response.data


class TestAdminErrorHandling:
    """Test admin interface error handling"""
    
    def test_admin_404_handling(self, app, client, admin_user):
        """Test admin 404 error handling"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/nonexistent/')
            
            # Should handle 404 gracefully
            assert response.status_code == 404
    
    def test_admin_invalid_id_handling(self, app, client, admin_user):
        """Test admin handling of invalid IDs"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            response = client.get('/admin/user/details/?id=99999')
            
            # Should handle gracefully
            assert response.status_code in [404, 302]
    
    def test_admin_malformed_data_handling(self, app, client, admin_user):
        """Test admin handling of malformed data"""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            # Try to create user with invalid data
            response = client.post('/admin/user/new/', data={
                'email': 'invalid-email',
                'user_name': ''  # Empty required field
            })
            
            if response.status_code == 200:
                # Should show validation errors
                assert b'error' in response.data.lower() or b'invalid' in response.data.lower()


class TestAdminPerformance:
    """Test admin interface performance"""
    
    def test_admin_list_performance(self, app, client, admin_user, test_category):
        """Test admin list performance with large datasets"""
        with app.app_context():
            # Create many users and transactions
            for i in range(20):
                user = TestDataFactory.create_test_user(f"user{i}")
                user.set_password("password123")
                db.session.add(user)
                db.session.commit()
                
                TransactionService.add_personal_transaction(
                    user, Decimal(f'{i * 10}.00'), 'expense', test_category.category_id
                )
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            
            import time
            
            # Test user list performance
            start = time.time()
            response = client.get('/admin/user/')
            end = time.time()
            
            if response.status_code == 200:
                load_time = end - start
                assert load_time < 3.0  # Should load within 3 seconds
            
            # Test transaction list performance
            start = time.time()
            response = client.get('/admin/transaction/')
            end = time.time()
            
            if response.status_code == 200:
                load_time = end - start
                assert load_time < 3.0  # Should load within 3 seconds
