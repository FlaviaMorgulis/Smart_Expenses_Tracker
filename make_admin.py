#!/usr/bin/env python3
"""
Script to make a user an administrator
Usage: python make_admin.py <email>
"""

import sys
from app import create_app, db
from app.models import User

def make_user_admin(email):
    """Make a user an administrator by email"""
    app = create_app()
    
    with app.app_context():
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return False
            
        if user.is_admin:
            print(f"User '{email}' is already an administrator.")
            return True
            
        # Make user admin
        user.is_admin = True
        db.session.commit()
        
        print(f"Success: User '{email}' is now an administrator.")
        return True

def list_users():
    """List all users in the system"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the system.")
            return
            
        print("Current users:")
        print("-" * 50)
        for user in users:
            admin_status = "Admin" if user.is_admin else "Regular"
            print(f"Email: {user.email}")
            print(f"Name: {user.user_name}")
            print(f"Status: {admin_status}")
            print("-" * 50)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python make_admin.py <email>     - Make user admin")
        print("  python make_admin.py --list      - List all users")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_users()
    else:
        email = sys.argv[1]
        make_user_admin(email)