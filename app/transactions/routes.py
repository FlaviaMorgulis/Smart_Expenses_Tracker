from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, make_response, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, Category, Budget
from datetime import datetime, timedelta
from app.services import BudgetService, SimpleAnalyticsService, ExportService 
import json

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/')
@login_required
def transactions():
    from .forms import TransactionForm 
    
    form = TransactionForm()
    
    categories = Category.query.filter_by(user_id=None).all()
    form.category_id.choices = [(0, 'Select Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    user_transactions = Transaction.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Transaction.transaction_date.desc()).all()
    
    return render_template('transactions.html', 
                         form=form, 
                         transactions=user_transactions)

@transactions_bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    from .forms import TransactionForm 

    form = TransactionForm()
    
    categories = Category.query.filter_by(user_id=None).all()
    form.category_id.choices = [(0, 'Select Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
            if form.transaction_type.data == 'expense':
                if not form.category_id.data or form.category_id.data == 0:
                    flash('Category is required for expenses', 'error')
                    return redirect(url_for('transactions.transactions'))
            
            category_id = form.category_id.data if form.category_id.data != 0 else None
            
            transaction = Transaction(
                user_id=current_user.user_id,
                amount=form.amount.data,
                transaction_type=form.transaction_type.data,
                category_id=category_id,
                transaction_date=form.transaction_date.data
            )
            
            db.session.add(transaction)
            db.session.commit()
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('transactions.transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding transaction. Please try again.', 'error')
            print(f"Transaction error: {e}")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('transactions.transactions'))

@transactions_bp.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    from .forms import EditTransactionForm 

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.user_id
    ).first_or_404()
    
    initial_data = {
        'amount': transaction.amount,
        'transaction_type': transaction.transaction_type,
        'transaction_date': transaction.transaction_date,
        'category_id': transaction.category_id if transaction.category_id is not None else 0
    }

    form = EditTransactionForm(data=initial_data)
    
    categories = Category.query.filter_by(user_id=None).all()
    form.category_id.choices = [(0, 'Select Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
            if form.transaction_type.data == 'expense':
                if not form.category_id.data or form.category_id.data == 0:
                    flash('Category is required for expenses', 'error')
                    return render_template('edit_transaction.html', form=form, transaction=transaction)
            
            transaction.amount = form.amount.data
            transaction.transaction_type = form.transaction_type.data
            transaction.category_id = form.category_id.data if form.category_id.data != 0 else None
            transaction.transaction_date = form.transaction_date.data
            
            db.session.commit()
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('transactions.transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating transaction.', 'error')
            print(f"Edit transaction error: {e}")
    
    return render_template('edit_transaction.html', 
                         form=form, 
                         transaction=transaction)

@transactions_bp.route('/delete_transaction/<int:transaction_id>', methods=['POST', 'DELETE'])
@login_required
def delete_transaction(transaction_id):
    try:
        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id,
            user_id=current_user.user_id
        ).first_or_404()
        
        if transaction:
            db.session.delete(transaction)
            db.session.commit()
            flash('Transaction deleted successfully!', 'success')
        else:
            flash('Transaction not found.', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash('Error deleting transaction.', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('transactions.transactions'))

@transactions_bp.route('/api/transaction_stats')
@login_required
def transaction_stats():
    try:
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.user_id,
            Transaction.transaction_type == 'income'
        ).scalar() or 0
        
        total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar() or 0
        
        current_balance = float(total_income) - float(total_expenses)
        
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_count = Transaction.query.filter(
            Transaction.user_id == current_user.user_id,
            Transaction.transaction_date >= thirty_days_ago
        ).count()
        
        return jsonify({
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'current_balance': current_balance,
            'recent_transactions': recent_count
        })
    except Exception as e:
        print(f"API error: {e}")
        return jsonify({
            'total_income': 0,
            'total_expenses': 0,
            'current_balance': 0,
            'recent_transactions': 0
        })

@transactions_bp.route('/api/category_spending')
@login_required
def category_spending():
    try:
        category_data = db.session.query(
            Category.category_name,
            db.func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == current_user.user_id,
            Transaction.transaction_type == 'expense'
        ).group_by(Category.category_name).all()
        
        result = [{'category': cat, 'amount': float(amount)} for cat, amount in category_data]
        return jsonify(result)
    except Exception as e:
        print(f"Category spending API error: {e}")
        return jsonify([])

@transactions_bp.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    from .forms import BudgetForm
    form = BudgetForm()
    
    categories = Category.query.filter_by(user_id=None).all()
    form.category_id.choices = [(0, 'Select Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
            if form.budget_type.data == 'total':
                # Total budget - category_id NULL
                BudgetService.create_or_update_total_budget(
                    user_id=current_user.user_id,
                    budget_amount=form.budget_amount.data,
                    alert_threshold=form.alert_threshold.data
                )
                flash('Total budget saved successfully!', 'success')
            else:
                # Category budget
                BudgetService.create_or_update_budget(
                    user_id=current_user.user_id,
                    budget_amount=form.budget_amount.data,
                    category_id=form.category_id.data,
                    alert_threshold=form.alert_threshold.data
                )
                flash('Category budget saved successfully!', 'success')
            
            return redirect(url_for('transactions.budgets'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error saving budget.', 'error')
            print(f"Budget error: {e}")
    
    # Get user budgets
    user_budgets = Budget.query.filter_by(user_id=current_user.user_id, is_active=True).all()
    
    return render_template('budgets.html', 
                         form=form, 
                         budgets=user_budgets)

@transactions_bp.route('/api/budget_alerts')
@login_required
def budget_alerts():
    from app.services import BudgetService
    alerts = BudgetService.check_budget_alerts(current_user.user_id)
    return jsonify(alerts)

@transactions_bp.route('/api/monthly_comparison')
@login_required
def monthly_comparison():
    from app.services import SimpleAnalyticsService
    import datetime
    
    now = datetime.datetime.now()
    monthly_data = []
    
    for i in range(6):
        month = now.month - i
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
            
        data = SimpleAnalyticsService.get_monthly_totals(current_user.user_id, year, month)
        monthly_data.append({
            'month': f"{year}-{month:02d}",
            'income': data['income'],
            'expenses': data['expenses']
        })
    
    monthly_data.reverse()
    return jsonify(monthly_data)

@transactions_bp.route('/export/csv')
@login_required
def export_csv():
    from app.services import ExportService
    csv_data = ExportService.export_transactions_to_csv(current_user.user_id)
    
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@transactions_bp.route('/export/pdf')
@login_required
def export_pdf():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from io import BytesIO
        from datetime import datetime
        
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        pdf.drawString(50, 800, f"Transactions Export - {datetime.now().strftime('%Y-%m-%d')}")
        
        # Get ALL transactions
        transactions = Transaction.query.filter_by(user_id=current_user.user_id).all()
        
        y = 770
        for transaction in transactions:
            # Simple format: Date | Type | Category | Amount
            line = f"{transaction.transaction_date.strftime('%Y-%m-%d')} | {transaction.transaction_type} | {transaction.category.category_name if transaction.category else 'Other'} | £{transaction.amount}"
            pdf.drawString(50, y, line)
            y -= 15
            
            # New page if needed
            if y < 50:
                pdf.showPage()
                y = 800
        
        pdf.save()
        buffer.seek(0)
        
        return send_file(
            buffer, 
            as_attachment=True, 
            download_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        flash(f'PDF Error: {str(e)}', 'error')
        return redirect(url_for('main.cash_flow'))
