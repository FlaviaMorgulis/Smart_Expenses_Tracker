from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, Category
from datetime import datetime, timedelta
import json

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/')
@login_required
def transactions():
    """Show all transactions for the current user"""
    from .forms import TransactionForm 
    
    form = TransactionForm()
    
    categories = Category.query.filter_by(user_id=None).all()
    form.category_id.choices = [(0, 'No Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    user_transactions = Transaction.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Transaction.transaction_date.desc()).all()
    
    return render_template('transactions.html', 
                         form=form, 
                         transactions=user_transactions)

@transactions_bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    """Add a new transaction"""
    from .forms import TransactionForm 

    form = TransactionForm()
    
    categories = Category.query.filter_by(user_id=None).all()
    form.category_id.choices = [(0, 'No Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
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
    """Edit an existing transaction"""
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
    form.category_id.choices = [(0, 'No Category')] + [(cat.category_id, cat.category_name) for cat in categories]
    
    if form.validate_on_submit():
        try:
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
    """Delete a transaction - SIMPLE VERSION"""
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
    """API endpoint for transaction statistics"""
    try:
        # Total income
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.user_id,
            Transaction.transaction_type == 'income'
        ).scalar() or 0
        
        # Total expenses
        total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar() or 0
        
        # Current balance
        current_balance = float(total_income) - float(total_expenses)
        
        # Recent transactions count (last 30 days)
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
    """API endpoint for category-wise spending"""
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
