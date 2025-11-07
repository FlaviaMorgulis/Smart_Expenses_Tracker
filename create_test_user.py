#!/usr/bin/env python3
"""
Create a simple test user for the Smart Expenses Tracker application
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(email='testuser@demo.com').first()
        if existing_user:
            print("Test user already exists!")
            print("Email: testuser@demo.com")
            print("Password: demo123")
            return
        
        # Create test user
        test_user = User(
            user_name='Demo User',
            email='testuser@demo.com',
            password_hash=generate_password_hash('demo123'),
            is_admin=False
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created successfully!")
            print("📧 Email: testuser@demo.com")
            print("🔑 Password: demo123")
            print("\nYou can now login with these credentials to see all the styled pages!")
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_test_user()