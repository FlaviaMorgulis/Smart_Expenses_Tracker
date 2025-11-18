#!/usr/bin/env python3
"""Create admin user"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    
    with app.app_context():
        # Check if admin exists
        existing = User.query.filter_by(email='admin@test.com').first()
        
        if existing:
            # Update password to ensure it's correct
            existing.set_password('Admin123!')
            db.session.commit()
            print(" Admin password updated!")
            print(" Email: admin@test.com")
            print(" Password: Admin123!")
            return
        
        # Create admin user with strong password
        admin = User(
            user_name='Admin User',
            email='admin@test.com',
            is_admin=True
        )
        admin.set_password('Admin123!')
        
        db.session.add(admin)
        db.session.commit()
        
        print(" Admin user created successfully!")
        print(" Email: admin@test.com")
        print(" Password: Admin123!")

if __name__ == '__main__':
    create_admin()
