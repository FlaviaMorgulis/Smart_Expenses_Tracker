from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
from app.auth.forms import SignupForm, LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Find user by email
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check password and log in
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    # If form validation fails, show login page again
    signup_form = SignupForm()
    return render_template('index.html', login_form=form, signup_form=signup_form, active_tab='login')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = SignupForm()
    
    if form.validate_on_submit():
        # Check if user already exists
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Email already registered', 'error')
            return render_template('index.html', login_form=LoginForm(), signup_form=form, active_tab='signup')
        
        # Create new user
        user = User(
            user_name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
    else:
        # Show form errors
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return render_template('index.html', login_form=LoginForm(), signup_form=form, active_tab='signup')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))
