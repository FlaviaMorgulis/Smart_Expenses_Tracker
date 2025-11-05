# Test Configuration File
# pytest configuration and shared fixtures for Smart Expenses Tracker

import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Category, Member, Transaction, Budget
from app.services import CategoryService, UserService
import time

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "SECRET_KEY": "test-secret-key"
    })
    
    with app.app_context():
        db.create_all()
        # Initialize system categories
        CategoryService.initialize_system_categories()
        yield app
        
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands"""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user_email = f"test_{int(time.time())}@example.com"
        existing_user = User.query.filter_by(email=user_email).first()
        if existing_user:
            return existing_user
            
        user = User(
            user_name="Test User",
            email=user_email
        )
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()
        
        # Return a fresh query to avoid detachment
        return User.query.filter_by(email=user_email).first()

@pytest.fixture
def admin_user(app):
    """Create a test admin user"""
    with app.app_context():
        # Check if admin already exists
        admin_email = f"admin_{int(time.time())}@example.com"
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            return existing_admin
            
        admin = User(
            user_name="Admin User",
            email=admin_email,
            is_admin=True
        )
        admin.set_password("adminpassword123")
        db.session.add(admin)
        db.session.commit()
        
        # Return a fresh query to avoid detachment
        return User.query.filter_by(email=admin_email).first()

@pytest.fixture
def test_category(app):
    """Create a test category"""
    with app.app_context():
        # Get or create a system category
        category = Category.query.filter_by(category_name='Food', user_id=None).first()
        if not category:
            category = CategoryService.create_category('Food', user_id=None)
        return category

@pytest.fixture
def test_member(app, test_user):
    """Create a test member"""
    with app.app_context():
        member = Member(
            user_id=test_user.user_id,
            name="Test Family Member",
            relationship="spouse"
        )
        db.session.add(member)
        db.session.commit()
        return member

@pytest.fixture
def logged_in_user(client, test_user):
    """Log in a test user and return the client"""
    response = client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    assert response.status_code in [200, 302]  # Success or redirect
    return client

@pytest.fixture
def logged_in_admin(client, admin_user):
    """Log in an admin user and return the client"""
    response = client.post('/login', data={
        'email': admin_user.email,
        'password': 'adminpassword123'
    })
    assert response.status_code in [200, 302]  # Success or redirect
    return client

class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_test_user(email_suffix="test"):
        """Create a test user with unique email"""
        user = User(
            user_name=f"Test User {email_suffix}",
            email=f"{email_suffix}_{int(time.time())}@example.com"
        )
        user.set_password("testpassword123")
        return user
    
    @staticmethod
    def create_test_transaction(user_id, category_id, amount=50.00, transaction_type='expense'):
        """Create a test transaction"""
        from decimal import Decimal
        from datetime import datetime
        
        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal(str(amount)),
            transaction_type=transaction_type,
            transaction_date=datetime.now()
        )
        return transaction
    
    @staticmethod
    def create_test_budget(user_id, category_id=None, amount=500.00):
        """Create a test budget"""
        from decimal import Decimal
        
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            budget_amount=Decimal(str(amount)),
            budget_period='monthly'
        )
        return budget

# Custom assertions for testing
class CustomAssertions:
    """Custom assertion methods for testing"""
    
    @staticmethod
    def assert_user_authenticated(response):
        """Assert that user is properly authenticated"""
        assert response.status_code != 401
        assert b'login' not in response.data.lower()
    
    @staticmethod
    def assert_admin_access(response):
        """Assert that admin has proper access"""
        assert response.status_code == 200
        assert b'admin' in response.data.lower() or b'Admin' in response.data
    
    @staticmethod
    def assert_access_denied(response):
        """Assert that access is properly denied"""
        assert response.status_code in [401, 403, 302]  # Unauthorized, Forbidden, or Redirect
    
    @staticmethod
    def assert_transaction_created(user_id, expected_amount):
        """Assert that a transaction was created correctly"""
        transaction = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).first()
        assert transaction is not None
        assert float(transaction.amount) == expected_amount

# Test utilities
class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def clean_database():
        """Clean all test data from database"""
        db.session.query(Transaction).delete()
        db.session.query(Budget).delete()
        db.session.query(Member).delete()
        db.session.query(User).filter(User.email.like('%@example.com')).delete()
        db.session.commit()
    
    @staticmethod
    def create_sample_data(user):
        """Create sample data for testing"""
        # Create a member
        member = Member(user_id=user.user_id, name="Sample Member", relationship="child")
        db.session.add(member)
        
        # Create some transactions
        category = Category.query.filter_by(category_name='Food').first()
        if category:
            transaction = TestDataFactory.create_test_transaction(
                user.user_id, category.category_id, 100.00
            )
            db.session.add(transaction)
        
        db.session.commit()
        return member

# Performance testing utilities
class PerformanceTestUtils:
    """Utilities for performance testing"""
    
    @staticmethod
    def time_database_operation(operation_func, *args, **kwargs):
        """Time a database operation"""
        import time
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def assert_query_performance(execution_time, max_time=1.0):
        """Assert that a query executes within acceptable time"""
        assert execution_time < max_time, f"Query took {execution_time:.3f}s, expected < {max_time}s"

# Test configuration constants
class TestConfig:
    """Configuration constants for testing"""
    
    # Performance thresholds
    MAX_QUERY_TIME = 1.0  # seconds
    MAX_PAGE_LOAD_TIME = 2.0  # seconds
    
    # Test data limits
    MAX_TEST_USERS = 100
    MAX_TEST_TRANSACTIONS = 1000
    
    # Security test constants
    INVALID_PASSWORDS = ["123", "", "short", "no_numbers", "NO_LOWERCASE"]
    INVALID_EMAILS = ["invalid", "@invalid.com", "invalid@", ""]
    
    # Valid test data
    VALID_PASSWORD = "ValidPassword123"
    VALID_EMAIL_DOMAIN = "@example.com"