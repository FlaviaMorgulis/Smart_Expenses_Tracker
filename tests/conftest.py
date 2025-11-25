"""Pytest configuration and fixtures"""
import pytest
from app import create_app, db
from app.models import User, Category, Member, Transaction, Budget
from datetime import datetime


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    with app.app_context():
        db.create_all()
        # Create system categories matching your app
        categories = ['Transport', 'Utilities', 'Entertainment',
                      'Food', 'Healthcare', 'Shopping', 'Other']
        for cat_name in categories:
            category = Category(category_name=cat_name, user_id=None)
            db.session.add(category)
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            user_name='Test User',
            email='testuser@example.com',
            is_admin=False
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        user_id = user.user_id

    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture
def admin_user(app):
    """Create an admin user"""
    with app.app_context():
        admin = User(
            user_name='Admin User',
            email='admin@test.com',
            is_admin=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.user_id

    with app.app_context():
        return User.query.get(admin_id)


@pytest.fixture
def auth_client(client, test_user):
    """Create authenticated test client"""
    with client:
        client.post('/login', data={
            'email': 'testuser@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        yield client


@pytest.fixture
def test_category(app):
    """Get Food category"""
    with app.app_context():
        category = Category.query.filter_by(category_name='Food').first()
        return category.category_id if category else None


@pytest.fixture
def test_member(app, test_user):
    """Create a test family member"""
    with app.app_context():
        member = Member(
            user_id=test_user.user_id,
            name='Sarah Johnson',
            relationship='Spouse'
        )
        db.session.add(member)
        db.session.commit()
        member_id = member.member_id

    with app.app_context():
        return Member.query.get(member_id)
