from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.auth.forms import LoginForm, SignupForm

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    login_form = LoginForm()
    signup_form = SignupForm()
    return render_template('index.html', login_form=login_form, signup_form=signup_form)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/transactions')
@login_required
def transactions():
    return "Transactions page - to be implemented"

@main.route('/profile')
@login_required
def profile():
    return "Profile page - to be implemented"

@main.route('/faq')
@login_required
def faq():
    return render_template('faq.html', user=current_user)
