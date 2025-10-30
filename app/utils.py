# Utility functions - Pure helper functions only
# Business logic should be in services.py
import re
from datetime import datetime, timedelta

def format_currency(amount):
    """Format amount as currency string"""
    return f"${amount:.2f}"

def calculate_percentage(part, total):
    """Calculate percentage with division by zero protection"""
    if total == 0:
        return 0
    return (part / total) * 100

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_transaction_amount(amount):
    """Validate transaction amount"""
    try:
        amount = float(amount)
        return amount > 0
    except (ValueError, TypeError):
        return False

def get_date_range_filter(start_date, end_date):
    """Helper to create date range filters for queries"""
    filters = []
    if start_date:
        filters.append(('transaction_date', '>=', start_date))
    if end_date:
        filters.append(('transaction_date', '<=', end_date))
    return filters

def sanitize_filename(filename):
    """Sanitize filename for safe file export"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename.strip()

def generate_csv_export(data, filename):
    """Generate CSV export from data dictionary"""
    import csv
    import io

    output = io.StringIO()

    # You can expand this based on  data structure
    if 'personal_transactions' in data:
        writer = csv.writer(output)
        writer.writerow(['Date', 'Amount', 'Type', 'Category'])

        for transaction in data['personal_transactions']:
            writer.writerow([
                transaction['date'],
                transaction['amount'],
                transaction['type'],
                transaction['category']
            ])

    return output.getvalue()

class DateHelper:
    """Helper class for date operations"""

    @staticmethod
    def get_month_start_end(year, month):
        """Get start and end dates for a given month"""
        from datetime import datetime
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        return start_date, end_date

    @staticmethod
    def get_current_month():
        """Get current month and year"""
        from datetime import datetime
        now = datetime.now()
        return now.year, now.month

    @staticmethod
    def format_date_for_display(date):
        """Format date for user display"""
        return date.strftime('%Y-%m-%d %H:%M')

class TransactionHelper:
    """Helper class for transaction operations"""

    @staticmethod
    def calculate_net_balance(transactions):
        """Calculate net balance from a list of transactions"""
        income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        return income - expenses

    @staticmethod
    def group_transactions_by_category(transactions):
        """Group transactions by category"""
        grouped = {}
        for transaction in transactions:
            category = transaction.category.category_name if transaction.category else 'Uncategorized'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(transaction)
        return grouped

    @staticmethod
    def filter_transactions_by_type(transactions, transaction_type):
        """Filter transactions by type (income/expense)"""
        return [t for t in transactions if t.transaction_type == transaction_type]

class ValidationHelper:
    """Helper class for data validation"""

    @staticmethod
    def validate_user_data(name, email, password):
        """Validate user registration data"""
        errors = []

        if not name or len(name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")

        if not validate_email(email):
            errors.append("Invalid email format")

        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long")

        return errors


class QueryPerformanceHelper:
    """Helper class for query optimization and monitoring"""
    
    @staticmethod
    def time_query(query_func, *args, **kwargs):
        """Measure query execution time for performance monitoring"""
        import time
        start_time = time.time()
        result = query_func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            'result': result,
            'execution_time_seconds': execution_time,
            'execution_time_ms': execution_time * 1000,
            'performance_rating': 'Fast' if execution_time < 0.1 else 'Medium' if execution_time < 0.5 else 'Slow'
        }
    
    @staticmethod
    def optimize_transaction_query(user_id, start_date=None, end_date=None, category_id=None):
        """Optimized transaction query with proper indexing usage"""
        from app.models import Transaction
        
        # Use indexes efficiently
        query = Transaction.query.filter(Transaction.user_id == user_id)
        
        # Use compound index (user_id, transaction_date)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Use index (category_id, transaction_type)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        
        return query
    
    @staticmethod
    def get_query_statistics():
        """Get basic database statistics for monitoring"""
        from app.models import Transaction, User, Category, Budget
        
        return {
            'total_users': User.query.count(),
            'total_transactions': Transaction.query.count(),
            'total_categories': Category.query.count(),
            'total_budgets': Budget.query.count(),
            'system_categories': Category.query.filter_by(user_id=None).count(),
            'user_categories': Category.query.filter(Category.user_id.isnot(None)).count()
        }

    @staticmethod
    def validate_transaction_data(amount, transaction_type, category_id=None):
        """Validate transaction data"""
        errors = []

        if not validate_transaction_amount(amount):
            errors.append("Amount must be a positive number")

        if transaction_type not in ['income', 'expense']:
            errors.append("Transaction type must be 'income' or 'expense'")

        return errors

    @staticmethod
    def validate_member_data(name, relationship):
        """Validate member data"""
        errors = []

        if not name or len(name.strip()) < 2:
            errors.append("Member name must be at least 2 characters long")

        if not relationship or len(relationship.strip()) < 2:
            errors.append("Relationship must be specified")

        return errors