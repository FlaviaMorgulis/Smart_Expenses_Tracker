# Smart Expenses Tracker - Services Layer
from datetime import datetime, timedelta
from . import db
from .models import User, Category, Transaction, Member, Budget, MembersTransaction

class CategoryService:
    """Simple category management"""
    
    @staticmethod
    def get_all_categories():
        """Get all categories"""
        return Category.query.all()
    
    @staticmethod
    def get_category_by_id(category_id):
        """Get category by ID"""
        return Category.query.get(category_id)
    
    @staticmethod
    def create_category(category_name, user_id=None):
        """Create new category - Note: Categories are Enum-constrained in this model"""
        # This model uses Enum constraint, so only predefined categories can be created
        valid_categories = ['Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other']
        
        if category_name not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        
        category = Category(
            category_name=category_name,  
            user_id=user_id  # None for system categories
        )
        db.session.add(category)
        db.session.commit()
        return category
    
    @staticmethod
    def get_system_categories():
        """Get all system categories (user_id is None)"""
        return Category.query.filter_by(user_id=None).all()
    
    @staticmethod 
    def get_categories_by_name(category_name):
        """Get categories by name"""
        return Category.query.filter_by(category_name=category_name).all()
    
    @staticmethod
    def initialize_system_categories():
        """Initialize system categories if they don't exist - compatible with seed script"""
        system_categories = ['Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other']
        created_count = 0
        
        for category_name in system_categories:
            existing = Category.query.filter_by(category_name=category_name, user_id=None).first()
            if not existing:
                try:
                    CategoryService.create_category(category_name, user_id=None)
                    created_count += 1
                except Exception as e:
                    print(f"Error creating {category_name}: {e}")
                    
        return created_count


class UserService:
    """Basic user management"""
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def create_user(username, email, password_hash):
        """Create new user"""
        user = User(
            user_name=username,  # Model uses user_name, not username
            email=email,
            password_hash=password_hash
        )
        db.session.add(user)
        db.session.commit()
        return user


class TransactionService:
    """Basic transaction management"""
    
    @staticmethod
    def get_user_transactions(user_id):
        """Get all transactions for a user"""
        return Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.transaction_date.desc()
        ).all()
    
    @staticmethod
    def get_transaction_by_id(transaction_id):
        """Get transaction by ID"""
        return Transaction.query.get(transaction_id)
    
    @staticmethod
    def create_transaction(user_id, amount, category_id, transaction_type, transaction_date=None):
        """Create new transaction - Note: This model doesn't have description field"""
        if not transaction_date:
            transaction_date = datetime.now()
            
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            category_id=category_id,
            transaction_type=transaction_type,
            transaction_date=transaction_date
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
    
    @staticmethod
    def delete_transaction(transaction_id):
        """Delete a transaction"""
        transaction = Transaction.query.get(transaction_id)
        if transaction:
            db.session.delete(transaction)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_recent_transactions(user_id, limit=10):
        """Get recent transactions for user"""
        return Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.transaction_date.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_recent_transactions_table_data(user_id, limit=10):
        """Get recent transactions formatted for table display - beginner version"""
        transactions = TransactionService.get_recent_transactions(user_id, limit)
        
        table_data = []
        for t in transactions:
            row = {
                'transaction_id': t.transaction_id,
                'date': t.transaction_date.strftime('%Y-%m-%d'),
                'category': t.category.category_name if t.category else 'Uncategorized',
                'type': t.transaction_type.title(),
                'amount': f"${float(t.amount):.2f}",
                'amount_raw': float(t.amount),
                'is_personal': t.is_personal_transaction(),
                'member_count': len(t.get_associated_members()),
                'members': [member.name for member in t.get_associated_members()]
            }
            table_data.append(row)
        
        return table_data


class SimpleAnalyticsService:
    """Basic analytics - what a beginner could implement"""
    
    @staticmethod
    def get_total_income(user_id):
        """Get total income for user"""
        transactions = Transaction.query.filter_by(
            user_id=user_id, 
            transaction_type='income'
        ).all()
        return sum(float(t.amount) for t in transactions)
    
    @staticmethod
    def get_total_expenses(user_id):
        """Get total expenses for user"""
        transactions = Transaction.query.filter_by(
            user_id=user_id, 
            transaction_type='expense'
        ).all()
        return sum(float(t.amount) for t in transactions)
    
    @staticmethod
    def get_balance(user_id):
        """Get current balance (income - expenses)"""
        income = SimpleAnalyticsService.get_total_income(user_id)
        expenses = SimpleAnalyticsService.get_total_expenses(user_id)
        return income - expenses
    
    @staticmethod
    def get_monthly_totals(user_id, year, month):
        """Get income/expense totals for specific month"""
        # Simple date filtering
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        ).all()
        
        income = sum(float(t.amount) for t in transactions if t.transaction_type == 'income')
        expenses = sum(float(t.amount) for t in transactions if t.transaction_type == 'expense')
        
        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses,
            'transaction_count': len(transactions)
        }
    
    @staticmethod
    def get_spending_by_category(user_id):
        """Get simple spending breakdown by category"""
        transactions = Transaction.query.filter_by(
            user_id=user_id,
            transaction_type='expense'
        ).all()
        
        category_totals = {}
        for transaction in transactions:
            category_name = transaction.category.category_name if transaction.category else 'Other'
            if category_name in category_totals:
                category_totals[category_name] += float(transaction.amount)
            else:
                category_totals[category_name] = float(transaction.amount)
        
        return category_totals


class BudgetService:
    """Simplified budget management"""
    
    @staticmethod
    def create_simple_budget(user_id, category_id, amount, budget_period='monthly'):
        """Create a simple budget"""
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            budget_amount=amount,
            budget_period=budget_period,
            is_active=True
        )
        db.session.add(budget)
        db.session.commit()
        return budget
    
    @staticmethod
    def get_user_budgets(user_id):
        """Get all budgets for user"""
        return Budget.query.filter_by(user_id=user_id, is_active=True).all()
    
    @staticmethod
    def check_budget_status(user_id, category_id):
        """Simple budget check - see if user is over budget"""
        budget = Budget.query.filter_by(
            user_id=user_id, 
            category_id=category_id, 
            is_active=True
        ).first()
        
        if not budget:
            return None
        
        # Get current month spending for this category
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        spent = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_of_month
        ).all()
        
        total_spent = sum(float(t.amount) for t in spent)
        budget_amount = float(budget.budget_amount)
        
        return {
            'budget_amount': budget_amount,
            'spent': total_spent,
            'remaining': budget_amount - total_spent,
            'is_over_budget': total_spent > budget_amount,
            'percentage_used': (total_spent / budget_amount * 100) if budget_amount > 0 else 0
        }
    
    @staticmethod
    def check_budget_alerts(user_id):
        """Simple budget alerts for beginner version"""
        budgets = BudgetService.get_user_budgets(user_id)
        alerts = []
        
        for budget in budgets:
            status = BudgetService.check_budget_status(user_id, budget.category_id)
            if status and status['is_over_budget']:
                alerts.append({
                    'budget_id': budget.budget_id,  # Model uses budget_id, not id
                    'category_name': budget.category.category_name if budget.category else 'Unknown',
                    'message': f"Over budget in {budget.category.category_name if budget.category else 'category'}",
                    'spent': status['spent'],
                    'budget_amount': status['budget_amount'],
                    'percentage_used': status['percentage_used']
                })
        
        return alerts


class MemberService:
    """Basic member management"""
    
    @staticmethod
    def get_user_members(user_id):
        """Get all members for a user"""
        return Member.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def create_member(user_id, name, email=None):
        """Create new member"""
        member = Member(
            user_id=user_id,
            name=name,
            email=email
        )
        db.session.add(member)
        db.session.commit()
        return member
    
    @staticmethod
    def get_member_by_id(member_id):
        """Get member by ID"""
        return Member.query.get(member_id)


class DashboardService:
    """Simple dashboard data"""
    
    @staticmethod
    def get_dashboard_summary(user_id):
        """Get basic dashboard information"""
        # Get current month data
        now = datetime.now()
        current_month_data = SimpleAnalyticsService.get_monthly_totals(
            user_id, now.year, now.month
        )
        
        # Get recent transactions using table format
        recent_transactions_data = TransactionService.get_recent_transactions_table_data(user_id, 5)
        
        # Get active budgets count and alerts
        budgets = BudgetService.get_user_budgets(user_id)
        budget_alerts = BudgetService.check_budget_alerts(user_id)
        
        return {
            'monthly_income': current_month_data['income'],
            'monthly_expenses': current_month_data['expenses'],
            'monthly_balance': current_month_data['balance'],
            'recent_transactions': recent_transactions_data,
            'active_budgets_count': len(budgets),
            'budget_alerts_count': len(budget_alerts),
            'budget_alerts': budget_alerts,
            'current_month': now.strftime('%B %Y')
        }


#  Export Service
class ExportService:
    """Basic data export functionality"""
    
    @staticmethod
    def export_transactions_to_csv(user_id):
        """Simple CSV export of transactions"""
        transactions = TransactionService.get_user_transactions(user_id)
        
        csv_data = "Date,Category,Type,Amount,Members,Personal\n"
        for t in transactions:
            members_count = len(t.get_associated_members())
            csv_data += f"{t.transaction_date.strftime('%Y-%m-%d')},"
            csv_data += f"{t.category.category_name if t.category else 'Other'},"
            csv_data += f"{t.transaction_type},{t.amount},"
            csv_data += f"{members_count},{t.is_personal_transaction()}\n"
        
        return csv_data


# Utilities
class UtilityService:
    """Helper functions for common tasks"""
    
    @staticmethod
    def format_currency(amount):
        """Format amount as currency"""
        return f"${float(amount):.2f}"
    
    @staticmethod
    def get_current_month_name():
        """Get current month name"""
        return datetime.now().strftime('%B')
    
    @staticmethod
    def get_date_range_for_month(year, month):
        """Get start and end dates for a month"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        return start_date, end_date
    
    @staticmethod
    def calculate_percentage(part, total):
        """Calculate percentage safely"""
        if total == 0:
            return 0
        return (part / total) * 100


class ReportingService:
    """Simple reporting functionality for documentation requirements"""
    
    @staticmethod
    def get_category_report(user_id):
        """Get category spending report for reports page"""
        category_breakdown = SimpleAnalyticsService.get_spending_by_category(user_id)
        
        # Format for reports page display
        formatted_report = []
        total_expenses = sum(category_breakdown.values())
        
        for category, amount in category_breakdown.items():
            percentage = UtilityService.calculate_percentage(amount, total_expenses)
            formatted_report.append({
                'category_name': category,
                'amount': amount,
                'amount_formatted': UtilityService.format_currency(amount),
                'percentage': percentage,
                'progress_width': min(percentage, 100)  # Cap at 100% for progress bars
            })
        
        return {
            'categories': formatted_report,
            'total_expenses': total_expenses,
            'total_expenses_formatted': UtilityService.format_currency(total_expenses)
        }
    
    @staticmethod
    def get_monthly_report(user_id, year, month):
        """Get monthly spending report"""
        monthly_data = SimpleAnalyticsService.get_monthly_totals(user_id, year, month)
        category_data = SimpleAnalyticsService.get_spending_by_category(user_id)
        
        return {
            'period': f"{year}-{month:02d}",
            'monthly_totals': monthly_data,
            'category_breakdown': category_data,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class CashFlowService:
    """Simple cash flow analysis for documentation requirements"""
    
    @staticmethod
    def get_cash_flow_summary(user_id):
        """Get cash flow overview data for cash flow page"""
        # Get basic totals
        total_income = SimpleAnalyticsService.get_total_income(user_id)
        total_expenses = SimpleAnalyticsService.get_total_expenses(user_id)
        net_cash_flow = total_income - total_expenses
        
        # Get current month data
        now = datetime.now()
        current_month_data = SimpleAnalyticsService.get_monthly_totals(user_id, now.year, now.month)
        
        return {
            'summary': {
                'total_income': total_income,
                'total_income_formatted': UtilityService.format_currency(total_income),
                'total_expenses': total_expenses,
                'total_expenses_formatted': UtilityService.format_currency(total_expenses),
                'net_cash_flow': net_cash_flow,
                'net_cash_flow_formatted': UtilityService.format_currency(net_cash_flow),
                'cash_flow_positive': net_cash_flow >= 0
            },
            'current_month': {
                'income': current_month_data['income'],
                'expenses': current_month_data['expenses'],
                'balance': current_month_data['balance'],
                'income_formatted': UtilityService.format_currency(current_month_data['income']),
                'expenses_formatted': UtilityService.format_currency(current_month_data['expenses']),
                'balance_formatted': UtilityService.format_currency(current_month_data['balance'])
            }
        }


class FamilyExpenseService:
    """Simple family expense tracking for documentation requirements"""
    
    @staticmethod
    def get_family_dashboard(user_id):
        """Get family expense dashboard data"""
        # Get all user members
        members = MemberService.get_user_members(user_id)
        
        # Get recent shared transactions (transactions with members)
        all_transactions = TransactionService.get_user_transactions(user_id)
        shared_transactions = [t for t in all_transactions if not t.is_personal_transaction()]
        recent_shared = sorted(shared_transactions, key=lambda x: x.transaction_date, reverse=True)[:5]
        
        # Calculate total family expenses
        total_family_expenses = sum(float(t.amount) for t in shared_transactions if t.transaction_type == 'expense')
        
        # Format member data
        member_data = []
        for member in members:
            member_transactions = [t for t in shared_transactions if any(mt.member_id == member.member_id for mt in t.members)]
            member_expense_total = sum(float(t.get_cost_per_person()) for t in member_transactions if t.transaction_type == 'expense')
            
            member_data.append({
                'member_id': member.member_id,
                'name': member.name,
                'relationship': member.relationship,
                'total_expenses': member_expense_total,
                'total_expenses_formatted': UtilityService.format_currency(member_expense_total),
                'transaction_count': len(member_transactions)
            })
        
        # Format recent shared transactions for table
        recent_shared_formatted = []
        for t in recent_shared:
            recent_shared_formatted.append({
                'transaction_id': t.transaction_id,
                'date': t.transaction_date.strftime('%Y-%m-%d'),
                'category': t.category.category_name if t.category else 'Other',
                'amount': float(t.amount),
                'amount_formatted': UtilityService.format_currency(float(t.amount)),
                'members': [member.name for member in t.get_associated_members()],
                'cost_per_person': t.get_cost_per_person(),
                'cost_per_person_formatted': UtilityService.format_currency(t.get_cost_per_person())
            })
        
        return {
            'family_summary': {
                'total_family_expenses': total_family_expenses,
                'total_family_expenses_formatted': UtilityService.format_currency(total_family_expenses),
                'member_count': len(members),
                'shared_transaction_count': len(shared_transactions)
            },
            'members': member_data,
            'recent_shared_transactions': recent_shared_formatted
        }


