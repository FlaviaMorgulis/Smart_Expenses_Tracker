"""
Main Routes Module
==================
This module contains all main application routes organized by functionality:
- General Pages (index, about, dashboard)
- Cash Flow & Analytics
- User Profile
- Family Management (members, family expenses)
- Budget Management
- API Endpoints
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, User, Category, Budget
from app.auth.forms import LoginForm, SignupForm
from datetime import datetime, timedelta
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf import FlaskForm
from app.services import CashFlowService, SimpleAnalyticsService, ReportingService, BudgetService, CategoryService

main_bp = Blueprint('main', __name__)


# ============================================================================
# GENERAL PAGES
# ============================================================================

@main_bp.route('/')
def index():
    """Landing page - redirects to dashboard if authenticated"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    login_form = LoginForm()
    signup_form = SignupForm()
    return render_template('index.html', login_form=login_form, signup_form=signup_form)


@main_bp.route('/about')
@login_required
def about():
    """About page"""
    return render_template('about.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime
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
            start_date = now - timedelta(days=150)  # ~5 months
        else:
            if time_range == '3months':
                start_date = now - timedelta(days=90)   # ~3 months
            elif time_range == '6months':
                start_date = now - timedelta(days=150)  # ~5 months
            elif time_range == '1year':
                start_date = now - timedelta(days=330)  # ~11 months
            elif time_range == '2years':
                start_date = now - timedelta(days=690)  # ~23 months
            elif time_range == 'all':
                start_date = oldest_transaction.transaction_date.replace(day=1)
            else:
                start_date = now - timedelta(days=150)  # ~5 months
        
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
            
            # Move to next month (approximately 30 days)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        if len(monthly_comparison) > 24:
            monthly_comparison = monthly_comparison[-24:]
        
        # Simplified category spending - use existing method
        category_spending = SimpleAnalyticsService.get_spending_by_category(current_user.user_id)
        
        # Simplified budget alerts for now
        try:
            budget_alerts = BudgetService.get_user_budget_alerts(current_user.user_id)
        except:
            budget_alerts = []
        
        # Simplified budget calculation for now
        try:
            total_budget_status = BudgetService.get_total_budget_status(current_user.user_id)
            if total_budget_status:
                remaining_budget = total_budget_status['remaining']
                total_budget = total_budget_status['budget_amount']
            else:
                remaining_budget = monthly_balance
                total_budget = 0
        except:
            remaining_budget = monthly_balance
            total_budget = 0
        
        # Calculate total balance (all-time income - all-time expenses)
        balance = SimpleAnalyticsService.get_balance(current_user.user_id)
        income = SimpleAnalyticsService.get_total_income(current_user.user_id)
        expenses = SimpleAnalyticsService.get_total_expenses(current_user.user_id)

        return render_template('dashboard.html',
                             user=current_user,
                             balance=balance,
                             income=income,
                             expenses=expenses,
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
                             balance=0,
                             income=0,
                             expenses=0,
                             monthly_income=0,
                             monthly_expenses=0,
                             remaining_budget=0,
                             total_budget=0,
                             current_month=datetime.now().strftime('%B %Y'),
                             current_month_short=datetime.now().strftime('%b'),
                             monthly_comparison=[],
                             category_spending={},
                             budget_alerts=[],
                             current_time_range='6months')


@main_bp.route('/faq')
@login_required
def faq():
    """FAQ page"""
    return render_template('faq_new.html')


# ============================================================================
# CASH FLOW & ANALYTICS
# ============================================================================

@main_bp.route('/cashflow')
@login_required
def cash_flow():
    """Cash flow analysis page with income/expense tracking"""
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


# ============================================================================
# USER PROFILE
# ============================================================================

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page with statistics and account information"""
    # Get user statistics
    transaction_count = Transaction.query.filter_by(user_id=current_user.user_id).count()
    
    total_spent_query = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense'
    ).scalar()
    total_spent = total_spent_query if total_spent_query else 0
    
    categories_used = db.session.query(Transaction.category_id).filter_by(
        user_id=current_user.user_id
    ).distinct().count()
    
    # Calculate days active (days since first transaction)
    first_transaction = Transaction.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Transaction.transaction_date.asc()).first()
    
    days_active = 0
    if first_transaction:
        days_active = (datetime.now().date() - first_transaction.transaction_date.date()).days
    
    return render_template('profile.html',
                         transaction_count=transaction_count,
                         total_spent=total_spent,
                         categories_used=categories_used,
                         days_active=days_active)


# ============================================================================
# FAMILY MANAGEMENT
# ============================================================================

@main_bp.route('/members')
@login_required
def members():
    """Redirect to the new family management page"""
    return redirect(url_for('main.family_management'))


@main_bp.route('/family_management')
@login_required
def family_management():
    """Comprehensive family management page with members, expenses, and budgets"""
    from app.models import Member, Category
    from datetime import datetime, timedelta
    
    # Get user's family members
    family_members = Member.query.filter_by(user_id=current_user.user_id).all()
    
    # Calculate basic stats
    member_count = len(family_members)
    
    # Get total expenses (all expenses, not just family/shared ones)
    total_expenses_query = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense'
    ).scalar()
    
    total_family_expenses = float(total_expenses_query) if total_expenses_query else 0
    
    # Family budget total - get from active user budgets
    # First try to get total budget (category_id is None)
    total_budget = Budget.query.filter(
        Budget.user_id == current_user.user_id,
        Budget.is_active == True,
        Budget.category_id == None
    ).first()
    
    if total_budget:
        family_budget_total = float(total_budget.budget_amount)
    else:
        # If no total budget, sum all category budgets
        category_budgets_sum = db.session.query(db.func.sum(Budget.budget_amount)).filter(
            Budget.user_id == current_user.user_id,
            Budget.is_active == True,
            Budget.category_id != None
        ).scalar()
        family_budget_total = float(category_budgets_sum) if category_budgets_sum else 0
    
    budget_percentage = (total_family_expenses / family_budget_total * 100) if family_budget_total > 0 else 0
    
    # Get member contribution data
    member_contributions = []
    for member in family_members:
        stats = member.get_lifetime_stats()
        member_contributions.append({
            'name': member.name,
            'total_contribution': float(stats['total_contribution']),
            'transaction_count': stats['total_transactions']
        })
    
    # Category data (include all expenses, not just family expenses)
    category_data = db.session.query(
        Category.category_name,
        db.func.sum(Transaction.amount).label('total_amount')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense'
    ).group_by(Category.category_name).all()
    
    category_chart_data = [{'category': cat[0], 'amount': float(cat[1])} for cat in category_data]
    
    # Create category expenses dictionary for budget section
    category_expenses = {}
    for cat in category_data:
        category_expenses[cat[0]] = float(cat[1])
    
    # Get category-specific budgets from database (only non-zero budgets)
    category_budgets = {}
    category_budget_records = Budget.query.filter(
        Budget.user_id == current_user.user_id,
        Budget.is_active == True,
        Budget.category_id != None  # Category-specific budgets
    ).all()
    
    for budget in category_budget_records:
        if budget.category and budget.budget_amount > 0:
            category_budgets[budget.category.category_name] = float(budget.budget_amount)
    
    # Per-member category data from actual transactions
    per_member_category_data = {}
    
    # Get current user's share of expenses (only expenses where they participated)
    user_spending_by_category = {}
    user_transactions = Transaction.query.filter_by(
        user_id=current_user.user_id,
        transaction_type='expense'
    ).all()
    
    for transaction in user_transactions:
        if transaction.category and transaction.user_participates:
            cat_name = transaction.category.category_name
            # Calculate user's share of this expense
            cost_per_person = transaction.get_cost_per_person()
            
            if cat_name in user_spending_by_category:
                user_spending_by_category[cat_name] += cost_per_person
            else:
                user_spending_by_category[cat_name] = cost_per_person
    
    user_spending_list = []
    for cat_name, amount in user_spending_by_category.items():
        if amount > 0:
            user_spending_list.append({'category': cat_name, 'amount': float(amount)})
    
    if user_spending_list:
        per_member_category_data[current_user.user_name or 'You'] = user_spending_list
    
    # For family members, show their portion of shared expenses
    for member in family_members:
        member_expenses = []
        # Get transactions this member participated in (via MembersTransaction junction table)
        for mt in member.transactions:
            transaction = mt.transaction  # Access actual Transaction object
            if transaction.transaction_type == 'expense' and transaction.category:
                cat_name = transaction.category.category_name
                # Calculate member's share
                cost_per_person = transaction.get_cost_per_person()
                
                # Find or create category entry
                existing = next((e for e in member_expenses if e['category'] == cat_name), None)
                if existing:
                    existing['amount'] += cost_per_person
                else:
                    member_expenses.append({'category': cat_name, 'amount': cost_per_person})
        
        if member_expenses:
            per_member_category_data[member.name] = member_expenses
    
    # Recent expenses (both personal and family expenses)
    recent_shared_expenses = db.session.query(Transaction).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense'
    ).order_by(Transaction.transaction_date.desc()).limit(10).all()
    
    recent_expenses_data = []
    for transaction in recent_shared_expenses:
        member_names = [member.name for member in transaction.get_associated_members()]
        recent_expenses_data.append({
            'id': transaction.transaction_id,
            'date': transaction.transaction_date.strftime('%b %d, %Y'),
            'description': 'Family Expense',
            'category': transaction.category.category_name if transaction.category else 'Other',
            'amount': float(transaction.amount),
            'cost_per_person': transaction.get_cost_per_person(),
            'members': member_names,
            'member_count': len(member_names) + (1 if transaction.user_participates else 0)
        })
    
    # Get all categories for the form dropdowns
    all_categories = Category.query.all()
    
    return render_template('family_management.html',
                         members=family_members,
                         member_count=member_count,
                         total_family_expenses=total_family_expenses,
                         family_budget_total=family_budget_total,
                         budget_percentage=budget_percentage,
                         member_contributions=member_contributions,
                         category_chart_data=category_chart_data,
                         per_member_category_data=per_member_category_data,
                         category_expenses=category_expenses,
                         category_budgets=category_budgets,
                         recent_shared_expenses=recent_expenses_data,
                         categories=all_categories)


# ----------------------------------------------------------------------------
# Family Member Management Routes
# ----------------------------------------------------------------------------

@main_bp.route('/add_member', methods=['POST'])
@login_required
def add_member():
    """Add a new family member"""
    from app.models import Member
    
    name = request.form.get('name')
    relationship = request.form.get('relationship')
    
    if name and relationship:
        new_member = Member(
            user_id=current_user.user_id,
            name=name,
            relationship=relationship
        )
        db.session.add(new_member)
        db.session.commit()
        flash(f'Family member {name} added successfully!', 'success')
    else:
        flash('Please provide both name and relationship.', 'error')
    return redirect(url_for('main.family_management'))


@main_bp.route('/edit_member', methods=['POST'])
@login_required
def edit_member():
    """Edit an existing family member"""
    from app.models import Member
    
    member_id = request.form.get('member_id')
    name = request.form.get('name')
    relationship = request.form.get('relationship')
    
    if member_id and name and relationship:
        member = Member.query.filter_by(
            member_id=member_id,
            user_id=current_user.user_id
        ).first()
        
        if member:
            member.name = name
            member.relationship = relationship
            db.session.commit()
            flash(f'Family member updated successfully!', 'success')
        else:
            flash('Member not found.', 'error')
    else:
        flash('Please provide all required information.', 'error')
    
    return redirect(url_for('main.family_management'))


@main_bp.route('/delete_member/<int:member_id>', methods=['POST'])
@login_required
def delete_member(member_id):
    """Delete a family member"""
    from app.models import Member
    
    member = Member.query.filter_by(
        member_id=member_id,
        user_id=current_user.user_id
    ).first()
    
    if member:
        db.session.delete(member)
        db.session.commit()
        flash(f'Family member {member.name} removed successfully!', 'success')
        return jsonify({'status': 'success'})
    else:
        flash('Member not found.', 'error')
        return jsonify({'status': 'error'}), 404


# ----------------------------------------------------------------------------
# Family Expense Management Routes
# ----------------------------------------------------------------------------

@main_bp.route('/add_family_expense', methods=['POST'])
@login_required
def add_family_expense():
    """Add a new family shared expense"""
    from app.models import Member, MembersTransaction
    from datetime import datetime
    
    try:
        description = request.form.get('description')  # Still get it from form but don't validate
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        expense_date = request.form.get('expense_date')
        member_ids = request.form.getlist('member_ids')
        include_user = request.form.get('include_user') == 'true'
        
        if amount and category_id:
            # Parse the date or use current date as fallback
            if expense_date:
                transaction_date = datetime.strptime(expense_date, '%Y-%m-%d')
            else:
                transaction_date = datetime.now()
            
            # Create the transaction
            new_transaction = Transaction(
                user_id=current_user.user_id,
                category_id=category_id,
                amount=float(amount),
                transaction_type='expense',
                user_participates=include_user,
                transaction_date=transaction_date
            )
            
            db.session.add(new_transaction)
            db.session.flush()  # Get the transaction ID
            
            # Add member associations
            for member_id in member_ids:
                member_transaction = MembersTransaction(
                    transaction_id=new_transaction.transaction_id,
                    member_id=int(member_id)
                )
                db.session.add(member_transaction)
            
            db.session.commit()
            flash('Family expense added successfully!', 'success')
        else:
            flash('Please provide all required information.', 'error')
    except Exception as e:
        flash(f'Error adding expense: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.family_management'))

@main_bp.route('/edit_family_expense', methods=['POST'])
@login_required
def edit_family_expense():
    """Edit an existing family shared expense"""
    from app.models import Member, MembersTransaction
    
    expense_id = request.form.get('expense_id')
    expense_date = request.form.get('expense_date')
    description = request.form.get('description')  # Still get it from form but don't validate
    amount = request.form.get('amount')
    category_id = request.form.get('category_id')
    member_ids = request.form.getlist('member_ids')
    include_user = request.form.get('include_user') == 'true'
    
    if expense_id and amount and category_id:
        # Get the existing transaction
        transaction = Transaction.query.filter_by(
            transaction_id=expense_id,
            user_id=current_user.user_id
        ).first()
        
        if transaction:
            # Update transaction details
            if expense_date:
                from datetime import datetime
                transaction.transaction_date = datetime.strptime(expense_date, '%Y-%m-%d')
            transaction.amount = float(amount)
            transaction.category_id = category_id
            transaction.user_participates = include_user
            
            # Clear existing member associations
            MembersTransaction.query.filter_by(
                transaction_id=transaction.transaction_id
            ).delete()
            
            # Add new member associations
            for member_id in member_ids:
                member_transaction = MembersTransaction(
                    transaction_id=transaction.transaction_id,
                    member_id=int(member_id)
                )
                db.session.add(member_transaction)
            
            db.session.commit()
            flash('Expense updated successfully!', 'success')
        else:
            flash('Expense not found.', 'error')
    else:
        flash('Please provide all required information.', 'error')
    
    return redirect(url_for('main.family_management'))


@main_bp.route('/get_expense/<int:expense_id>')
@login_required
def get_expense(expense_id):
    """Get expense details for editing (API endpoint)"""
    from app.models import MembersTransaction
    
    transaction = Transaction.query.filter_by(
        transaction_id=expense_id,
        user_id=current_user.user_id
    ).first()
    
    if transaction:
        # Get associated member IDs
        member_transactions = MembersTransaction.query.filter_by(
            transaction_id=transaction.transaction_id
        ).all()
        member_ids = [mt.member_id for mt in member_transactions]
        
        return jsonify({
            'id': transaction.transaction_id,
            'date': transaction.transaction_date.strftime('%Y-%m-%d'),
            'amount': float(transaction.amount),
            'category_id': transaction.category_id,
            'user_participates': transaction.user_participates,
            'member_ids': member_ids
        })
    else:
        return jsonify({'error': 'Expense not found'}), 404

@main_bp.route('/update_family_budget', methods=['POST'])
@login_required
def update_family_budget():
    """Create or update category budget for family management"""
    from app.services import BudgetService
    
    category_id = request.form.get('category_id')
    amount = request.form.get('amount')
    
    if not category_id or not amount:
        flash('Please select a category and enter an amount.', 'error')
        return redirect(url_for('main.family_management'))
    
    try:
        amount = float(amount)
        category_id = int(category_id)
        
        # Create or update the budget for this category (note: budget_amount comes before category_id)
        budget = BudgetService.create_or_update_budget(
            user_id=current_user.user_id,
            budget_amount=amount,
            category_id=category_id
        )
        
        flash('Category budget added successfully!', 'success')
    except ValueError as e:
        flash(f'Invalid amount or category: {str(e)}', 'error')
    except Exception as e:
        flash(f'Error creating budget: {str(e)}', 'error')
    
    return redirect(url_for('main.family_management'))


@main_bp.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Delete a family expense"""
    transaction = Transaction.query.filter_by(
        transaction_id=expense_id,
        user_id=current_user.user_id
    ).first()
    
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
        return jsonify({'status': 'success'})
    else:
        flash('Expense not found.', 'error')
        return jsonify({'status': 'error'}), 404


# ============================================================================
# BUDGET MANAGEMENT
# ============================================================================

@main_bp.route('/budget')
@login_required
def budget():
    """Budget management page with category budgets and alerts"""
    try:
        # Get all user budgets
        user_budgets = BudgetService.get_user_budgets(current_user.user_id)
        
        # Get all categories for budget creation
        categories = CategoryService.get_all_categories()
        
        # Calculate total budget and spent amounts
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get category spending data for current month
        category_spending = {}
        total_budget_amount = 0
        total_spent = 0
        
        for category in categories:
            # Get spending for this category this month
            category_spent_query = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.user_id,
                Transaction.transaction_type == 'expense',
                Transaction.category_id == category.category_id,
                Transaction.transaction_date >= start_of_month
            ).scalar()
            
            category_spent = float(category_spent_query) if category_spent_query else 0
            
            # Find budget for this category
            category_budget = next((b for b in user_budgets if b.category_id == category.category_id), None)
            budget_amount = float(category_budget.budget_amount) if category_budget else 0
            
            if budget_amount > 0 or category_spent > 0:  # Only include categories with budget or spending
                category_spending[category.category_name] = {
                    'budget': budget_amount,
                    'spent': category_spent,
                    'remaining': budget_amount - category_spent,
                    'percentage': (category_spent / budget_amount * 100) if budget_amount > 0 else 0,
                    'is_over_budget': category_spent > budget_amount and budget_amount > 0
                }
                
                total_budget_amount += budget_amount
                total_spent += category_spent
        
        # Calculate overall budget status
        overall_percentage = (total_spent / total_budget_amount * 100) if total_budget_amount > 0 else 0
        
        # Get budget alerts
        budget_alerts = BudgetService.check_budget_alerts(current_user.user_id)
        
        # Generate monthly trend data for chart (last 6 months)
        monthly_trends = []
        for i in range(5, -1, -1):  # Last 6 months
            month_date = (now - timedelta(days=i*30)).replace(day=1)
            month_start = month_date.replace(hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_spent_query = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.user_id,
                Transaction.transaction_type == 'expense',
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end
            ).scalar()
            
            month_spent = float(month_spent_query) if month_spent_query else 0
            
            monthly_trends.append({
                'month': month_date.strftime('%b'),
                'spent': month_spent,
                'budget': total_budget_amount  # Using current total budget for all months
            })
        
        return render_template('budget.html',
                             total_budget=total_budget_amount,
                             monthly_spent=total_spent,
                             remaining_budget=total_budget_amount - total_spent,
                             budget_percentage=overall_percentage,
                             category_spending=category_spending,
                             budget_alerts=budget_alerts,
                             monthly_trends=monthly_trends,
                             categories=categories,
                             current_month=now.strftime('%B %Y'))
                             
    except Exception as e:
        print(f"Error in budget route: {e}")
        # Fallback data
        return render_template('budget.html',
                             total_budget=0,
                             monthly_spent=0,
                             remaining_budget=0,
                             budget_percentage=0,
                             category_spending={},
                             budget_alerts=[],
                             monthly_trends=[],
                             categories=[],
                             current_month=now.strftime('%B %Y'))


@main_bp.route('/budget/add', methods=['POST'])
@login_required
def add_budget():
    """Add a new category budget"""
    try:
        data = request.get_json()
        category_id = int(data.get('category_id')) if data.get('category_id') else None
        amount = float(data.get('amount', 0))
        budget_period = data.get('budget_period', 'monthly')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid budget amount'}), 400
        
        # Use existing service method
        BudgetService.create_or_update_budget(
            user_id=current_user.user_id,
            budget_amount=amount,
            category_id=category_id,
            budget_period=budget_period
        )
        
        return jsonify({'success': True, 'message': 'Budget added successfully'})
    except Exception as e:
        print(f"Error adding budget: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/budget/<int:budget_id>/edit', methods=['POST'])
@login_required
def edit_budget(budget_id):
    """Edit an existing budget"""
    """Edit an existing budget"""
    try:
        budget = Budget.query.get_or_404(budget_id)
        
        # Verify ownership
        if budget.user_id != current_user.user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        amount = float(data.get('amount', 0)) if data.get('amount') else None
        budget_period = data.get('budget_period')
        
        if amount and amount > 0:
            budget.budget_amount = amount
        if budget_period:
            budget.budget_period = budget_period
        
        budget.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Budget updated successfully'})
    except Exception as e:
        print(f"Error editing budget: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/budget/<int:budget_id>/delete', methods=['POST'])
@login_required
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        budget = Budget.query.get_or_404(budget_id)
        
        # Verify ownership
        if budget.user_id != current_user.user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        db.session.delete(budget)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Budget deleted successfully'})
    except Exception as e:
        print(f"Error deleting budget: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# API ENDPOINTS
# ============================================================================

@main_bp.route('/api/annual_data')
@login_required
def annual_data():
    """API endpoint for annual financial data"""
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
