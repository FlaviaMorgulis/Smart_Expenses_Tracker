from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, User, Category, Budget
from app.auth.forms import LoginForm, SignupForm
from datetime import datetime, timedelta
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf import FlaskForm
from app.services import CashFlowService, SimpleAnalyticsService, ReportingService, BudgetService

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
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from app.models import Transaction
    now = datetime.now()
    
    try:
        # Get time range from request
        time_range = request.args.get('range', '6months')
        
        current_month_data = SimpleAnalyticsService.get_monthly_totals(current_user.user_id, now.year, now.month)
        
        monthly_income = current_month_data['income']
        monthly_expenses = current_month_data['expenses']
        monthly_balance = current_month_data['balance']
        
        # Get monthly comparison data based on selected time range
        monthly_comparison = []
        
        oldest_transaction = Transaction.query.filter_by(
            user_id=current_user.user_id
        ).order_by(Transaction.transaction_date.asc()).first()
        
        if not oldest_transaction:
            start_date = now - relativedelta(months=5)
        else:
            if time_range == '3months':
                start_date = now - relativedelta(months=2)
            elif time_range == '6months':
                start_date = now - relativedelta(months=5)
            elif time_range == '1year':
                start_date = now - relativedelta(months=11)
            elif time_range == '2years':
                start_date = now - relativedelta(months=23)
            elif time_range == 'all':
                start_date = oldest_transaction.transaction_date.replace(day=1)
            else:
                start_date = now - relativedelta(months=5)
        
        current_date = start_date.replace(day=1)
        end_date = now.replace(day=1)
        
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            
            monthly_data = SimpleAnalyticsService.get_monthly_totals(current_user.user_id, year, month)
            monthly_comparison.append({
                'month': f"{year}-{month:02d}",
                'month_name': datetime(year, month, 1).strftime('%b %Y'),
                'month_short': datetime(year, month, 1).strftime('%b'),
                'income': monthly_data['income'],
                'expenses': monthly_data['expenses']
            })
            
            current_date += relativedelta(months=1)
        
        if len(monthly_comparison) > 24:
            monthly_comparison = monthly_comparison[-24:]
        
        category_spending = {}
        if time_range == '3months':
            for i in range(3):
                target_date = now - relativedelta(months=i)
                monthly_categories = SimpleAnalyticsService.get_monthly_spending_by_category(
                    current_user.user_id, target_date.year, target_date.month
                )
                for category, amount in monthly_categories.items():
                    category_spending[category] = category_spending.get(category, 0) + amount
        elif time_range == '6months':
            for i in range(6):
                target_date = now - relativedelta(months=i)
                monthly_categories = SimpleAnalyticsService.get_monthly_spending_by_category(
                    current_user.user_id, target_date.year, target_date.month
                )
                for category, amount in monthly_categories.items():
                    category_spending[category] = category_spending.get(category, 0) + amount
        elif time_range == '1year':
            for i in range(12):
                target_date = now - relativedelta(months=i)
                monthly_categories = SimpleAnalyticsService.get_monthly_spending_by_category(
                    current_user.user_id, target_date.year, target_date.month
                )
                for category, amount in monthly_categories.items():
                    category_spending[category] = category_spending.get(category, 0) + amount
        elif time_range == '2years':
            for i in range(24):
                target_date = now - relativedelta(months=i)
                monthly_categories = SimpleAnalyticsService.get_monthly_spending_by_category(
                    current_user.user_id, target_date.year, target_date.month
                )
                for category, amount in monthly_categories.items():
                    category_spending[category] = category_spending.get(category, 0) + amount
        elif time_range == 'all':
            if oldest_transaction:
                current_date = oldest_transaction.transaction_date.replace(day=1)
                while current_date <= now.replace(day=1):
                    monthly_categories = SimpleAnalyticsService.get_monthly_spending_by_category(
                        current_user.user_id, current_date.year, current_date.month
                    )
                    for category, amount in monthly_categories.items():
                        category_spending[category] = category_spending.get(category, 0) + amount
                    current_date += relativedelta(months=1)
        else:
            # Default: current month
            category_spending = SimpleAnalyticsService.get_monthly_spending_by_category(
                current_user.user_id, now.year, now.month
            )
        
        print(f"Time range: {time_range}, Category spending: {category_spending}")
        
        # Get budget alerts for slider
        budget_alerts = BudgetService.get_user_budget_alerts(current_user.user_id)
        
        # Calculate remaining budget
        total_budget_status = BudgetService.get_total_budget_status(current_user.user_id)
        if total_budget_status:
            remaining_budget = total_budget_status['remaining']
            total_budget = total_budget_status['budget_amount']
        else:
            remaining_budget = monthly_balance
            total_budget = 0
        
        return render_template('dashboard.html',
                             user=current_user,
                             monthly_income=monthly_income,
                             monthly_expenses=monthly_expenses,
                             remaining_budget=remaining_budget,
                             total_budget=total_budget,
                             current_month=now.strftime('%B %Y'),
                             current_month_short=now.strftime('%b'),
                             monthly_comparison=monthly_comparison,
                             category_spending=category_spending,
                             budget_alerts=budget_alerts,
                             current_time_range=time_range)
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard.html',
                             user=current_user,
                             monthly_income=0,
                             monthly_expenses=0,
                             remaining_budget=0,
                             total_budget=0,
                             current_month=now.strftime('%B %Y'),
                             current_month_short=now.strftime('%b'),
                             monthly_comparison=[],
                             category_spending={},
                             budget_alerts=[],
                             current_time_range='6months')
    
@main_bp.route('/cashflow')
@login_required
def cash_flow():
    try:
        # Get cash flow summary
        cash_flow_data = CashFlowService.get_cash_flow_summary(current_user.user_id)

        # Get category report
        category_report = ReportingService.get_category_report(current_user.user_id)

        # Get available years from user's transactions
        available_years = db.session.query(
            db.func.extract('year', Transaction.transaction_date)
        ).filter(
            Transaction.user_id == current_user.user_id
        ).distinct().order_by(
            db.func.extract('year', Transaction.transaction_date).asc()
        ).all()
        
        available_years = [int(year[0]) for year in available_years]

        # Get yearly data only for years that have transactions
        yearly_data = []
        if available_years:
            for year in available_years:
                yearly_income = 0
                yearly_expenses = 0
                
                for month in range(1, 13):
                    try:
                        monthly_data = SimpleAnalyticsService.get_monthly_totals(current_user.user_id, year, month)
                        yearly_income += monthly_data['income']
                        yearly_expenses += monthly_data['expenses']
                    except Exception as e:
                        print(f"Error getting monthly data for {year}-{month}: {e}")
                        continue
                
                # Only add year if there's actual data
                if yearly_income > 0 or yearly_expenses > 0:
                    yearly_data.append({
                        'year': year,
                        'income': yearly_income,
                        'expenses': yearly_expenses,
                        'balance': yearly_income - yearly_expenses
                    })
        
        # If no yearly data, show current year
        if not yearly_data:
            current_year = datetime.now().year
            yearly_data.append({
                'year': current_year,
                'income': 0,
                'expenses': 0,
                'balance': 0
            })

        return render_template('cashflow.html',
                             cash_flow_data=cash_flow_data,
                             category_report=category_report,
                             yearly_data=yearly_data)
    
    except Exception as e:
        print(f"Cashflow error: {e}")
        
        # Return empty data
        current_year = datetime.now().year
        empty_data = {
            'summary': {
                'total_income': 0,
                'total_income_formatted': '£0.00',
                'total_expenses': 0,
                'total_expenses_formatted': '£0.00',
                'net_cash_flow': 0,
                'net_cash_flow_formatted': '£0.00',
                'cash_flow_positive': True
            },
            'current_month': {
                'income': 0,
                'expenses': 0,
                'balance': 0,
                'income_formatted': '£0.00',
                'expenses_formatted': '£0.00',
                'balance_formatted': '£0.00'
            }
        }
        
        empty_categories = {
            'categories': [],
            'total_expenses': 0,
                'total_expenses_formatted': '£0.00'
        }
        
        empty_yearly = [{
            'year': current_year,
            'income': 0,
            'expenses': 0,
            'balance': 0
        }]
        
        return render_template('cashflow.html',
                             cash_flow_data=empty_data,
                             category_report=empty_categories,
                             yearly_data=empty_yearly)
    
@main_bp.route('/profile')
@login_required
def profile():
    return "Profile page - to be implemented"

@main_bp.route('/faq')
@login_required
def faq():
    return render_template('faq.html', user=current_user)


@main_bp.route('/api/annual_data')
@login_required
def annual_data():
    """API for annual financial data"""
    from app.services import SimpleAnalyticsService
    import datetime
    
    current_year = datetime.datetime.now().year
    annual_data = []
    
    for month in range(1, 13):
        data = SimpleAnalyticsService.get_monthly_totals(current_user.user_id, current_year, month)
        annual_data.append({
            'month': month,
            'income': data['income'],
            'expenses': data['expenses'],
            'balance': data['balance']
        })
    
    return jsonify(annual_data)
