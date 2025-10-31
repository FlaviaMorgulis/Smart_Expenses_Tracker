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

# Users cannot create custom categories due to Enum constraint in Category model
# Users can only choose from the predefined system categories:
# 'Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other'

def get_available_categories():
    """Get all available categories (only system categories due to Enum constraint)"""
    # Only system categories are available due to Enum constraint in Category model
    return Category.query.filter_by(user_id=None).all()

def list_categories():
    """List all available categories (only system categories due to Enum constraint)"""
    print("\n Available Categories:")
    
    # Only system categories exist due to Enum constraint
    categories = Category.query.filter_by(user_id=None).all()
    print(f"\n System Categories ({len(categories)}):")
    for cat in categories:
        print(f"  • {cat.category_name}")
    
    print("\n Note: Users can only choose from these predefined categories due to Enum constraint.")

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