from app import create_app, db
from app.models import User
from app.auth.forms import LoginForm

app = create_app()

with app.app_context():
    # Test form validation
    form_data = {
        'email': 'admin@test.com',
        'password': 'admin123',
        'csrf_token': 'test'
    }
    
    form = LoginForm(data=form_data)
    
    print('=== Form Validation Test ===')
    print(f'Form data: {form_data}')
    print(f'Form is valid: {form.validate()}')
    print(f'Form errors: {form.errors}')
    
    # Test user lookup
    user = User.query.filter_by(email='admin@test.com').first()
    print(f'\n=== User Test ===')
    print(f'User found: {user is not None}')
    
    if user:
        print(f'Password check: {user.check_password("admin123")}')
        print(f'User authenticated: {user.is_authenticated}')
        print(f'User is admin: {user.is_admin}')