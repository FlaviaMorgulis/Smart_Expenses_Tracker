#!/usr/bin/env python3
"""
Fix database categories to match enum values
"""
from app import create_app, db

def fix_categories():
    app = create_app()
    with app.app_context():
        try:
            # Use SQLAlchemy 2.0 syntax
            from sqlalchemy import text
            
            # Update Transportation to Transport
            result1 = db.session.execute(text("""
                UPDATE categories 
                SET category_name = 'Transport' 
                WHERE category_name = 'Transportation'
            """))
            
            # Update Bills to Utilities if any exist
            result2 = db.session.execute(text("""
                UPDATE categories 
                SET category_name = 'Utilities' 
                WHERE category_name = 'Bills'
            """))
            
            # Commit the changes
            db.session.commit()
            
            print("✅ Categories updated successfully!")
            print(f"   Updated {result1.rowcount} Transportation → Transport")
            print(f"   Updated {result2.rowcount} Bills → Utilities")
            
            # Verify the changes
            result = db.session.execute(text("SELECT category_id, category_name FROM categories"))
            print("\nCurrent categories:")
            for row in result:
                print(f"  ID: {row[0]}, Name: {row[1]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_categories()