# services.py - Business logic and complex operations
from datetime import datetime
from sqlalchemy import func
from . import db

class CategoryService:
    """Handle category operations and business logic"""
    
    @staticmethod
    def initialize_default_categories():
        """Initialize default categories if they don't exist"""
        from .models import Category
        categories = ['Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other']

        for cat_name in categories:
            existing = Category.query.filter_by(category_name=cat_name).first()
            if not existing:
                category = Category(category_name=cat_name)
                db.session.add(category)

        db.session.commit()
        return True
    
    @staticmethod
    def get_all_categories():
        """Get all available categories"""
        from .models import Category
        return Category.query.all()

    @staticmethod
    def get_category_by_name(category_name):
        """Find category by name"""
        from .models import Category
        return Category.query.filter_by(category_name=category_name).first()

class UserService:
    """Handle complex user operations and business logic"""
    
    @staticmethod
    def add_member_to_user(user, name, relationship):
        """Add a new member to the user's group"""
        from .models import Member
        member = Member(
            user_id=user.user_id,
            name=name,
            relationship=relationship
        )
        db.session.add(member)
        db.session.commit()
        return member
    
    @staticmethod
    def remove_member_from_user(user, member_id):
        """Remove a member from the group"""
        from .models import Member
        member = Member.query.filter_by(member_id=member_id, user_id=user.user_id).first()
        if member:
            db.session.delete(member)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def delete_user_account(user):
        """Delete user account and all associated data"""
        db.session.delete(user)
        db.session.commit()
        return True
    
    @staticmethod
    def delete_all_user_data(user):
        """Delete all user data (transactions, members) but keep account"""
        from .models import Transaction, Member
        Transaction.query.filter_by(user_id=user.user_id).delete()
        Member.query.filter_by(user_id=user.user_id).delete()
        db.session.commit()
        return True

class TransactionService:
    """Handle transaction operations and business logic"""
    
    @staticmethod
    def add_personal_transaction(user, amount, transaction_type, category_id, transaction_date=None):
        """Add a personal transaction"""
        from .models import Transaction
        if transaction_date is None:
            transaction_date = datetime.now()
        
        transaction = Transaction(
            user_id=user.user_id,
            category_id=category_id,
            amount=amount,
            transaction_type=transaction_type,
            transaction_date=transaction_date
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
    
    @staticmethod
    def add_member_transaction(user, member_id, amount, transaction_type, category_id, transaction_date=None):
        """Add a transaction for a member"""
        from .models import Transaction, MembersTransaction
        if transaction_date is None:
            transaction_date = datetime.now()
        
        # Create the transaction
        transaction = Transaction(
            user_id=user.user_id,
            category_id=category_id,
            amount=amount,
            transaction_type=transaction_type,
            transaction_date=transaction_date
        )
        db.session.add(transaction)
        db.session.flush()  # To get the transaction_id
        
        # Link member to transaction
        member_transaction = MembersTransaction(
            transaction_id=transaction.transaction_id,
            member_id=member_id
        )
        db.session.add(member_transaction)
        db.session.commit()
        return transaction
    
    @staticmethod
    def get_personal_transactions(user, start_date=None, end_date=None):
        """Get personal transactions with optional date filtering"""
        from .models import Transaction
        query = Transaction.query.filter_by(user_id=user.user_id)
        
        # Filter out transactions that have members (i.e., personal only)
        query = query.filter(~Transaction.members.any())
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.all()
    
    @staticmethod
    def get_member_transactions(user, member_id=None, start_date=None, end_date=None):
        """Get member transactions with optional filtering"""
        from .models import Transaction, MembersTransaction
        query = Transaction.query.filter_by(user_id=user.user_id)
        query = query.join(MembersTransaction)
        
        if member_id:
            query = query.filter(MembersTransaction.member_id == member_id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.all()
    
    @staticmethod
    def delete_transaction(user, transaction_id):
        """Delete a transaction"""
        from .models import Transaction
        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id, 
            user_id=user.user_id
        ).first()
        if transaction:
            db.session.delete(transaction)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_transaction(user, transaction_id, amount=None, category_id=None, transaction_date=None):
        """Update a transaction"""
        from .models import Transaction
        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id, 
            user_id=user.user_id
        ).first()
        if transaction:
            if amount is not None:
                transaction.amount = amount
            if category_id is not None:
                transaction.category_id = category_id
            if transaction_date is not None:
                transaction.transaction_date = transaction_date
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def add_member_to_transaction(transaction, member_id):
        """Add a member to this transaction"""
        from .models import MembersTransaction
        
        # Check if member is already associated
        existing = MembersTransaction.query.filter_by(
            transaction_id=transaction.transaction_id,
            member_id=member_id
        ).first()
        
        if not existing:
            member_transaction = MembersTransaction(
                transaction_id=transaction.transaction_id,
                member_id=member_id
            )
            db.session.add(member_transaction)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def remove_member_from_transaction(transaction, member_id):
        """Remove a member from this transaction"""
        from .models import MembersTransaction
        member_transaction = MembersTransaction.query.filter_by(
            transaction_id=transaction.transaction_id,
            member_id=member_id
        ).first()
        
        if member_transaction:
            db.session.delete(member_transaction)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_shared_transactions(user_id):
        """Get all transactions that have members associated (shared transactions)"""
        from .models import Transaction, MembersTransaction
        return db.session.query(Transaction).join(MembersTransaction).filter(
            Transaction.user_id == user_id
        ).distinct().all()

class AnalyticsService:
    """Handle data analysis and reporting"""
    
    @staticmethod
    def get_spending_by_category(user, start_date=None, end_date=None, member_id=None):
        """Get spending breakdown by category"""
        from .models import Category, Transaction, MembersTransaction
        query = db.session.query(
            Category.category_name,
            func.sum(Transaction.amount).label('total_amount')
        ).join(Transaction, Category.category_id == Transaction.category_id)
        
        query = query.filter(Transaction.user_id == user.user_id)
        query = query.filter(Transaction.transaction_type == 'expense')
        
        if member_id:
            query = query.join(MembersTransaction).filter(MembersTransaction.member_id == member_id)
        else:
            # Personal expenses only
            query = query.filter(~Transaction.members.any())
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.group_by(Category.category_name).all()
    
    @staticmethod
    def get_monthly_summary(user, year, month):
        """Get monthly income and expense summary"""
        from .models import Transaction
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == user.user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        ).all()
        
        income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        
        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        }

class ExportService:
    """Handle data export and CSV generation"""
    
    @staticmethod
    def export_user_data(user, start_date=None, end_date=None):
        """Export user data as dictionary for CSV/report generation"""
        personal_transactions = TransactionService.get_personal_transactions(user, start_date, end_date)
        member_transactions = TransactionService.get_member_transactions(user, start_date=start_date, end_date=end_date)
        
        data = {
            'user_info': {
                'name': user.user_name,
                'email': user.email,
                'created_at': user.created_at
            },
            'members': [
                {
                    'name': member.name,
                    'relationship': member.relationship,
                    'joined_at': member.joined_at
                } for member in user.members
            ],
            'personal_transactions': [
                {
                    'amount': float(t.amount),
                    'type': t.transaction_type,
                    'category': t.category.category_name if t.category else 'Uncategorized',
                    'date': t.transaction_date,
                    'created_at': t.created_at
                } for t in personal_transactions
            ],
            'member_transactions': [
                {
                    'amount': float(t.amount),
                    'type': t.transaction_type,
                    'category': t.category.category_name if t.category else 'Uncategorized',
                    'date': t.transaction_date,
                    'member': next((mt.member.name for mt in t.members), 'Unknown'),
                    'created_at': t.created_at
                } for t in member_transactions
            ]
        }
        return data

class MemberService:
    """Handle member-specific operations"""
    
    @staticmethod
    def get_member_transactions(member, start_date=None, end_date=None):
        """Get all transactions for this member"""
        from .models import Transaction, MembersTransaction
        query = db.session.query(Transaction).join(MembersTransaction).filter(
            MembersTransaction.member_id == member.member_id
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.all()
    
    @staticmethod
    def get_member_total_expenses(member, start_date=None, end_date=None):
        """Get total expenses for this member"""
        from .models import Transaction, MembersTransaction
        query = db.session.query(func.sum(Transaction.amount)).join(MembersTransaction).filter(
            MembersTransaction.member_id == member.member_id,
            Transaction.transaction_type == 'expense'
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        result = query.scalar()
        return result if result else 0
    
    @staticmethod
    def get_member_transactions_summary(member_id):
        """Get summary of transactions for a specific member"""
        from .models import Transaction, MembersTransaction
        transactions = db.session.query(Transaction).join(MembersTransaction).filter(
            MembersTransaction.member_id == member_id
        ).all()
        
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        
        return {
            'total_transactions': len(transactions),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': total_income - total_expenses
        }
    
    @staticmethod
    def get_member_total_expenses(member, start_date=None, end_date=None):
        """Get total expenses for this member"""
        from .models import Transaction, MembersTransaction
        query = db.session.query(func.sum(Transaction.amount)).join(MembersTransaction).filter(
            MembersTransaction.member_id == member.member_id,
            Transaction.transaction_type == 'expense'
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        result = query.scalar()
        return result if result else 0
    
    @staticmethod
    def get_shared_transactions(user_id):
        """Get all transactions that have members associated (shared transactions)"""
        from .models import Transaction, MembersTransaction
        return db.session.query(Transaction).join(MembersTransaction).filter(
            Transaction.user_id == user_id
        ).distinct().all()

class CategoryService:
    """Handle category-specific operations"""
    
    @staticmethod
    def get_category_total_spending(category, user_id, start_date=None, end_date=None):
        """Get total spending in this category for a user"""
        from .models import Transaction
        query = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == category.category_id,
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'expense'
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        result = query.scalar()
        return result if result else 0
    
    @staticmethod
    def get_category_transaction_count(category, user_id, start_date=None, end_date=None):
        """Get number of transactions in this category for a user"""
        from .models import Transaction
        query = Transaction.query.filter(
            Transaction.category_id == category.category_id,
            Transaction.user_id == user_id
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.count()


class BudgetService:
    """Handle budget operations and tracking"""
    
    @staticmethod
    def create_user_budget(user_id, category_id, budget_amount, budget_period='monthly', start_date=None, end_date=None):
        """Create a budget for a user in a specific category (or total expenses if category_id is None)"""
        from .models import Budget
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = datetime.now().date()
        
        if not end_date:
            if budget_period == 'weekly':
                end_date = start_date + timedelta(weeks=1)
            elif budget_period == 'monthly':
                end_date = start_date + timedelta(days=30)
            elif budget_period == 'yearly':
                end_date = start_date + timedelta(days=365)
            else:
                end_date = start_date + timedelta(days=30)  # Default to monthly
        
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            budget_amount=budget_amount,
            budget_period=budget_period,
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(budget)
        db.session.commit()
        return budget
    
    @staticmethod
    def create_member_budget(member_id, category_id, budget_amount, budget_period='monthly', start_date=None, end_date=None):
        """Create a budget for a member in a specific category (or total expenses if category_id is None)"""
        from .models import Budget
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = datetime.now().date()
        
        if not end_date:
            if budget_period == 'weekly':
                end_date = start_date + timedelta(weeks=1)
            elif budget_period == 'monthly':
                end_date = start_date + timedelta(days=30)
            elif budget_period == 'yearly':
                end_date = start_date + timedelta(days=365)
            else:
                end_date = start_date + timedelta(days=30)
        
        budget = Budget(
            member_id=member_id,
            category_id=category_id,
            budget_amount=budget_amount,
            budget_period=budget_period,
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(budget)
        db.session.commit()
        return budget
    
    @staticmethod
    def create_user_total_budget(user_id, budget_amount, budget_period='monthly', start_date=None, end_date=None):
        """Create a total expenses budget for a user (across all categories)"""
        return BudgetService.create_user_budget(
            user_id=user_id, 
            category_id=None,  # None means total expenses
            budget_amount=budget_amount,
            budget_period=budget_period,
            start_date=start_date,
            end_date=end_date
        )
    
    @staticmethod
    def create_member_total_budget(member_id, budget_amount, budget_period='monthly', start_date=None, end_date=None):
        """Create a total expenses budget for a member (across all categories)"""
        return BudgetService.create_member_budget(
            member_id=member_id,
            category_id=None,  # None means total expenses
            budget_amount=budget_amount,
            budget_period=budget_period,
            start_date=start_date,
            end_date=end_date
        )


class AdvancedAnalyticsService:
    """Advanced analytics and predictive methods for learning purposes"""
    
    @staticmethod
    def get_spending_trends(user, months=6):
        """Calculate month-over-month spending trends"""
        from .models import Transaction
        from datetime import datetime, timedelta
        import calendar
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        monthly_data = []
        for i in range(months):
            month_start = end_date - timedelta(days=(i + 1) * 30)
            month_end = end_date - timedelta(days=i * 30)
            
            monthly_expenses = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user.user_id,
                Transaction.transaction_type == 'expense',
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < month_end
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'expenses': float(monthly_expenses),
                'month_name': calendar.month_name[month_start.month]
            })
        
        # Calculate trend (simple linear regression)
        if len(monthly_data) >= 2:
            values = [item['expenses'] for item in monthly_data]
            trend_direction = 'increasing' if values[0] < values[-1] else 'decreasing'
            avg_change = (values[-1] - values[0]) / len(values)
        else:
            trend_direction = 'stable'
            avg_change = 0
        
        return {
            'monthly_data': list(reversed(monthly_data)),
            'trend_direction': trend_direction,
            'average_monthly_change': avg_change,
            'total_period_expenses': sum(item['expenses'] for item in monthly_data)
        }
    
    @staticmethod
    def predict_next_month_spending(user):
        """Simple linear prediction based on last 3 months trends"""
        from .models import Transaction
        from datetime import datetime, timedelta
        
        # Get last 3 months data
        end_date = datetime.now()
        months_data = []
        
        for i in range(3):
            month_start = end_date - timedelta(days=(i + 1) * 30)
            month_end = end_date - timedelta(days=i * 30)
            
            monthly_expenses = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user.user_id,
                Transaction.transaction_type == 'expense',
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < month_end
            ).scalar() or 0
            
            months_data.append(float(monthly_expenses))
        
        if len(months_data) >= 2:
            # Simple linear trend calculation
            recent_avg = sum(months_data[:2]) / 2
            older_avg = sum(months_data[1:]) / 2
            trend = recent_avg - older_avg
            
            # Predict next month
            predicted = months_data[0] + trend
            confidence = 'high' if abs(trend) < months_data[0] * 0.2 else 'medium'
        else:
            predicted = months_data[0] if months_data else 0
            confidence = 'low'
        
        return {
            'predicted_amount': max(0, predicted),  # Don't predict negative
            'confidence_level': confidence,
            'based_on_months': len(months_data),
            'historical_data': months_data,
            'trend_amount': trend if len(months_data) >= 2 else 0
        }
    
    @staticmethod
    def get_category_insights(user, months=3):
        """Advanced category analysis with insights"""
        from .models import Transaction, Category
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Get category spending with statistical analysis
        category_stats = db.session.query(
            Category.category_name,
            func.sum(Transaction.amount).label('total'),
            func.avg(Transaction.amount).label('average'),
            func.count(Transaction.transaction_id).label('count'),
            func.max(Transaction.amount).label('max_transaction'),
            func.min(Transaction.amount).label('min_transaction')
        ).join(Transaction).filter(
            Transaction.user_id == user.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_date
        ).group_by(Category.category_name).all()
        
        total_spending = sum(float(stat.total) for stat in category_stats)
        
        insights = []
        for stat in category_stats:
            percentage = (float(stat.total) / total_spending * 100) if total_spending > 0 else 0
            avg_per_transaction = float(stat.average)
            
            # Generate insights
            insight_text = f"{stat.category_name}: {percentage:.1f}% of spending"
            if percentage > 30:
                insight_text += " (Major expense category)"
            elif percentage < 5:
                insight_text += " (Minor expense category)"
            
            if stat.count > months * 10:  # More than 10 transactions per month
                insight_text += " - High frequency"
            
            insights.append({
                'category': stat.category_name,
                'total_spent': float(stat.total),
                'percentage': percentage,
                'transaction_count': stat.count,
                'average_per_transaction': avg_per_transaction,
                'highest_transaction': float(stat.max_transaction),
                'lowest_transaction': float(stat.min_transaction),
                'insight': insight_text
            })
        
        # Sort by total spending
        insights.sort(key=lambda x: x['total_spent'], reverse=True)
        
        return {
            'period_months': months,
            'total_spending': total_spending,
            'category_insights': insights,
            'top_category': insights[0]['category'] if insights else 'None',
            'most_frequent_category': max(insights, key=lambda x: x['transaction_count'])['category'] if insights else 'None'
        }
    
    @staticmethod
    def get_budget_performance_analysis(user):
        """Analyze budget performance with recommendations"""
        from .models import Budget, Transaction
        from datetime import datetime
        
        active_budgets = Budget.query.filter_by(user_id=user.user_id, is_active=True).all()
        
        if not active_budgets:
            return {'message': 'No active budgets found', 'budgets': []}
        
        budget_analysis = []
        for budget in active_budgets:
            # Get budget usage
            usage = BudgetService.get_budget_usage(budget.budget_id)
            
            # Generate recommendations
            recommendations = []
            if usage['percentage_used'] > 100:
                recommendations.append("Budget exceeded! Consider reducing spending in this category.")
            elif usage['percentage_used'] > 80:
                recommendations.append("Approaching budget limit. Monitor spending closely.")
            elif usage['percentage_used'] < 50:
                recommendations.append("Good budget control. Consider allocating unused funds to savings.")
            
            # Performance rating
            if usage['percentage_used'] <= 80:
                performance = 'Excellent'
            elif usage['percentage_used'] <= 100:
                performance = 'Good'
            else:
                performance = 'Needs Improvement'
            
            budget_analysis.append({
                'budget_id': budget.budget_id,
                'category': budget.category.category_name if budget.category else 'Total Expenses',
                'budget_amount': float(budget.budget_amount),
                'amount_spent': usage['amount_spent'],
                'percentage_used': usage['percentage_used'],
                'performance_rating': performance,
                'recommendations': recommendations,
                'days_remaining': (budget.end_date - datetime.now().date()).days
            })
        
        return {
            'total_budgets': len(budget_analysis),
            'budget_analysis': budget_analysis,
            'overall_performance': 'Good' if all(b['percentage_used'] <= 100 for b in budget_analysis) else 'Needs Attention'
        }
    
    @staticmethod
    def get_user_budgets(user_id, active_only=True):
        """Get all budgets for a user"""
        from .models import Budget
        query = Budget.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_member_budgets(member_id, active_only=True):
        """Get all budgets for a member"""
        from .models import Budget
        query = Budget.query.filter_by(member_id=member_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_user_category_budgets(user_id, active_only=True):
        """Get category-specific budgets for a user"""
        from .models import Budget
        query = Budget.query.filter_by(user_id=user_id).filter(Budget.category_id.isnot(None))
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_user_total_budgets(user_id, active_only=True):
        """Get total expense budgets for a user"""
        from .models import Budget
        query = Budget.query.filter_by(user_id=user_id, category_id=None)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_member_category_budgets(member_id, active_only=True):
        """Get category-specific budgets for a member"""
        from .models import Budget
        query = Budget.query.filter_by(member_id=member_id).filter(Budget.category_id.isnot(None))
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_member_total_budgets(member_id, active_only=True):
        """Get total expense budgets for a member"""
        from .models import Budget
        query = Budget.query.filter_by(member_id=member_id, category_id=None)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_budget_usage(budget_id):
        """Calculate how much of the budget has been used"""
        from .models import Budget, Transaction, MembersTransaction
        budget = Budget.query.get_or_404(budget_id)
        
        # Query transactions in the budget period (for specific category or all categories)
        query = Transaction.query.filter(
            Transaction.transaction_date >= budget.start_date,
            Transaction.transaction_date <= budget.end_date,
            Transaction.transaction_type == 'expense'
        )
        
        # If it's a category budget, filter by category; if total budget, include all categories
        if budget.is_category_budget():
            query = query.filter(Transaction.category_id == budget.category_id)
        
        if budget.is_user_budget():
            # User budget - get personal transactions only
            query = query.filter(Transaction.user_id == budget.user_id)
            query = query.filter(~Transaction.members.any())  # No members associated
        elif budget.is_member_budget():
            # Member budget - get transactions where this member is involved
            query = query.join(MembersTransaction).filter(
                MembersTransaction.member_id == budget.member_id
            )
        
        transactions = query.all()
        total_spent = sum(float(t.amount) for t in transactions)
        budget_amount = float(budget.budget_amount)
        
        return {
            'budget_id': budget_id,
            'budget_amount': budget_amount,
            'amount_spent': total_spent,
            'amount_remaining': budget_amount - total_spent,
            'percentage_used': (total_spent / budget_amount * 100) if budget_amount > 0 else 0,
            'is_over_budget': total_spent > budget_amount,
            'transaction_count': len(transactions)
        }
    
    @staticmethod
    def update_budget(budget_id, **updates):
        """Update an existing budget"""
        from .models import Budget
        budget = Budget.query.get_or_404(budget_id)
        
        allowed_fields = ['budget_amount', 'budget_period', 'start_date', 'end_date', 'is_active']
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(budget, field, value)
        
        budget.updated_at = datetime.now()
        db.session.commit()
        return budget
    
    @staticmethod
    def deactivate_budget(budget_id):
        """Deactivate a budget"""
        from .models import Budget
        budget = Budget.query.get_or_404(budget_id)
        budget.is_active = False
        budget.updated_at = datetime.now()
        db.session.commit()
        return budget