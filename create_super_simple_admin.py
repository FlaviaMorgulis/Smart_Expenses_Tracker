from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Create a super simple admin
    email = 'admin@admin.com'
    password = '123456'
    
    # Remove if exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    
    # Create new admin
    admin = User(
        user_name='Admin',
        email=email,
        is_admin=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print("✅ Super simple admin created!")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")
    print("👑 Admin: True")