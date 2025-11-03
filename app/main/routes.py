from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, User, Category
from app.auth.forms import LoginForm, SignupForm
from datetime import datetime, timedelta
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf import FlaskForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    login_form = LoginForm()
    signup_form = SignupForm()
    return render_template('index.html', login_form=login_form, signup_form=signup_form)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'income'
    ).scalar() or 0
    
    total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense'
    ).scalar() or 0
    
    current_balance = float(total_income) - float(total_expenses)
    
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Transaction.transaction_date.desc()).limit(5).all()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense',
        db.extract('month', Transaction.transaction_date) == current_month,
        db.extract('year', Transaction.transaction_date) == current_year
    ).scalar() or 0
    
    monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'income',
        db.extract('month', Transaction.transaction_date) == current_month,
        db.extract('year', Transaction.transaction_date) == current_year
    ).scalar() or 0
    
    return render_template('dashboard.html', 
                         user=current_user,
                         balance=current_balance,
                         income=float(total_income),
                         expenses=float(total_expenses),
                         monthly_expenses=float(monthly_expenses),
                         monthly_income=float(monthly_income),
                         recent_transactions=recent_transactions)

@main_bp.route('/profile')
@login_required
def profile():
    return "Profile page - to be implemented"

@main_bp.route('/faq')
@login_required
def faq():
    return render_template('faq.html', user=current_user)
