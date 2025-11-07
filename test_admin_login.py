from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(email='admin@test.com').first()
    
    if user:
        print(f'✅ User found: {user.email}')
        print(f'👤 Name: {user.user_name}')  
        print(f'👑 Is Admin: {user.is_admin}')
        print(f'🔑 Password check (admin123): {user.check_password("admin123")}')
    else:
        print('❌ User not found')