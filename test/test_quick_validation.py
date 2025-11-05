"""
Quick test to validate current app functionality
"""
import pytest
from app import create_app, db
from app.models import User, Category

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # Create default categories  
        categories = ['Food', 'Transport', 'Utilities', 'Entertainment']
        for cat_name in categories:
            if not Category.query.filter_by(category_name=cat_name).first():
                category = Category(category_name=cat_name)
                db.session.add(category)
        db.session.commit()
        yield app

@pytest.fixture  
def client(app):
    return app.test_client()

def test_index_route(client):
    """Test that index route works"""
    response = client.get('/')
    assert response.status_code == 200

def test_login_route_get(client):
    """Test login route GET"""
    response = client.get('/login')
    assert response.status_code == 200

def test_signup_route_get(client):
    """Test signup route GET"""  
    response = client.get('/signup')
    assert response.status_code == 200

def test_dashboard_requires_login(client):
    """Test dashboard requires authentication"""
    response = client.get('/dashboard')
    assert response.status_code in [302, 401]  # Redirect to login or unauthorized

def test_user_creation_and_login(app, client):
    """Test complete user creation and login"""
    with app.app_context():
        # Create user directly in database (check if exists first)
        existing_user = User.query.filter_by(email='test@example.com').first()
        if not existing_user:
            user = User(user_name='Test User', email='test@example.com')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
        
        # Test login
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should be redirected to dashboard
        assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()