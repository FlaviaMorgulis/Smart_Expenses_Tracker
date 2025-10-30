"""
Seed Categories Script
Populates the database with default system categories and provides utilities for category management.
"""

from app import create_app, db
from app.models import Category, User
from sqlalchemy.exc import IntegrityError

# Default system categories (user_id = None for system categories)
DEFAULT_CATEGORIES = [
    'Transport',
    'Utilities', 
    'Entertainment',
    'Food',
    'Healthcare',
    'Shopping',
    'Other'
]

def seed_system_categories():
    """Create default system categories available to all users"""
    print(" Seeding system categories...")
    
    created_count = 0
    for category_name in DEFAULT_CATEGORIES:
        # Check if system category already exists
        existing = Category.query.filter_by(category_name=category_name, user_id=None).first()
        
        if not existing:
            try:
                category = Category(
                    category_name=category_name,
                    user_id=None  # System category
                )
                db.session.add(category)
                db.session.commit()
                created_count += 1
                print(f"  Created system category: {category_name}")
            except IntegrityError as e:
                db.session.rollback()
                print(f"   Error creating {category_name}: {e}")
        else:
            print(f"   System category already exists: {category_name}")
    
    print(f" Created {created_count} new system categories")
    return created_count

def create_user_category(user_id, category_name):
    """Create a custom category for a specific user"""
    
    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Check if user already has this category
    existing = Category.query.filter_by(category_name=category_name, user_id=user_id).first()
    if existing:
        raise ValueError(f"User {user.user_name} already has category '{category_name}'")
    
    # Check if it's a system category name
    system_category = Category.query.filter_by(category_name=category_name, user_id=None).first()
    if system_category:
        raise ValueError(f"'{category_name}' is a system category. Users cannot create custom categories with system names.")
    
    try:
        category = Category(
            category_name=category_name,
            user_id=user_id
        )
        db.session.add(category)
        db.session.commit()
        print(f" Created user category '{category_name}' for {user.user_name}")
        return category
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Error creating category: {e}")

def get_available_categories(user_id=None):
    """Get all categories available to a user (system + their custom categories)"""
    
    # System categories (available to all)
    system_categories = Category.query.filter_by(user_id=None).all()
    
    if user_id:
        # User's custom categories
        user_categories = Category.query.filter_by(user_id=user_id).all()
        return system_categories + user_categories
    else:
        return system_categories

def list_categories():
    """List all categories in the database"""
    print("\n All Categories:")
    
    # System categories
    system_categories = Category.query.filter_by(user_id=None).all()
    print(f"\n System Categories ({len(system_categories)}):")
    for cat in system_categories:
        print(f"  • {cat.category_name}")
    
    # User categories
    user_categories = Category.query.filter(Category.user_id.isnot(None)).all()
    if user_categories:
        print(f"\n User Categories ({len(user_categories)}):")
        for cat in user_categories:
            user = User.query.get(cat.user_id)
            print(f"  • {cat.category_name} (by {user.user_name if user else 'Unknown User'})")
    else:
        print("\n No user categories found")

def cleanup_categories():
    """Remove all categories (for testing/reset purposes)"""
    print(" Cleaning up all categories...")
    
    deleted_count = Category.query.delete()
    db.session.commit()
    
    print(f"  Deleted {deleted_count} categories")
    return deleted_count

def main():
    """Main function to run seeding"""
    app = create_app()
    
    with app.app_context():
        print(" Starting category seeding process...")
        
        # Create tables if they don't exist
        db.create_all()
        
        # Seed system categories
        seed_system_categories()
        
        # List all categories
        list_categories()
        
        print("\n Category seeding completed!")

if __name__ == '__main__':
    main()