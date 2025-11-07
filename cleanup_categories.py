#!/usr/bin/env python3
"""
Clean up duplicate categories
"""
from app import create_app, db

def cleanup_duplicates():
    app = create_app()
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Keep the first occurrence of each category and remove duplicates
            # First, let's see what we have
            result = db.session.execute(text("SELECT category_id, category_name FROM categories ORDER BY category_id"))
            categories = list(result)
            
            print("Current categories:")
            for cat in categories:
                print(f"  ID: {cat[0]}, Name: {cat[1]}")
            
            # Remove duplicate Transport entries (keep ID 1, remove 8 and 9)
            db.session.execute(text("DELETE FROM categories WHERE category_name = 'Transport' AND category_id > 1"))
            
            db.session.commit()
            
            print("\n✅ Duplicates removed!")
            
            # Verify final state
            result = db.session.execute(text("SELECT category_id, category_name FROM categories ORDER BY category_id"))
            print("\nFinal categories:")
            for row in result:
                print(f"  ID: {row[0]}, Name: {row[1]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    cleanup_duplicates()