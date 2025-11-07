#!/usr/bin/env python3
"""
Create a simple admin user for testing
"""

from app import create_app, db
from app.models import User

def create_simple_admin():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@test.com').first()
        if existing_admin:
            print("Admin already exists!")
            print("Email: admin@test.com")
            print("Password: admin123")
            print(f"Is Admin: {existing_admin.is_admin}")
            return existing_admin
        
        # Create admin user
        admin_user = User(
            user_name='Simple Admin',
            email='admin@test.com',
            is_admin=True
        )
        admin_user.set_password('admin123')
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print("📧 Email: admin@test.com")
            print("🔑 Password: admin123")
            print("👑 Admin Status: True")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            db.session.rollback()
            return None
        
        return admin_user

if __name__ == '__main__':
    create_simple_admin()