from datetime import datetime
from . import db
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin): 
    __tablename__ = 'users' 
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now()) 

    # Relationships ( for now we keep delete orphan ,
    # but to be changed into a solution for keeping the data for 3 months and after autodelete)
    members = db.relationship('Member', backref='user', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', cascade='all, delete-orphan')

    # Flask-Login required method
    def get_id(self):
        return str(self.user_id)

    # Authentication methods 
    def set_password(self, password):
        """Hash and set the password with random salt"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

# Serialization, API Responses and more
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
#  repr so it returns an unambiguos data and type of objetc
    def __repr__(self):
        return f'User {self.user_name}'

#Using cascade so when user is deleted the linking data is automaticcaly deleted-
# (Solution for starting stage- prioritizes user data privacy over transaction data preservation)
#Personalization within constraints: User can't customize the category name but choose from a list, to simplify analytics
class Category(db.Model): 
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.Enum('Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other', name='category_enum'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)  

    # Relationships
    #passive deletes so SQL relies on the database to handle deletions not SQLALchemy, so we keep transaction data even if category is deleted.
    transactions = db.relationship('Transaction', backref='category', passive_deletes=True)

    #using is_system_category to help business logic and help the frontend to distinguish between system and user categories!
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'user_id': self.user_id,
            'is_system_category': self.user_id is None 
        }

    def __repr__(self):
        return f'Category {self.category_name}'

class Member(db.Model):
    """
    Members are data entities managed by the User - they represent family members
    for expense tracking purposes. Members do NOT have their own accounts or login access.
    Only the User can create transactions and assign members to them.
    """
    __tablename__ = 'members'
    member_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # Display name (e.g., "Sarah Thompson")
    relationship = db.Column(db.String(100), nullable=False)  # Relationship to user (e.g., "Spouse", "Child")
    joined_at = db.Column(db.DateTime, nullable=False, server_default=func.now())  # When user added this member

    # Relationships - members are linked to transactions via MembersTransaction junction table
    transactions = db.relationship('MembersTransaction', back_populates='member', cascade='all, delete-orphan')

    def get_monthly_contribution(self, month, year):
        """Calculate this member's contribution for a specific month (user's perspective)"""
        from datetime import datetime
        from sqlalchemy import extract
        
        # Get transactions this member was involved in for the specified month
        monthly_transactions = []
        for mt in self.transactions:
            transaction = mt.transaction
            if (transaction.transaction_date.month == month and 
                transaction.transaction_date.year == year and 
                transaction.transaction_type == 'expense'):
                monthly_transactions.append(transaction)
        
        # Calculate member's share using equal cost splitting
        total_contribution = 0
        for transaction in monthly_transactions:
            cost_per_person = float(transaction.amount) / len(transaction.members)
            total_contribution += cost_per_person
        
        return total_contribution

    def get_lifetime_stats(self):
        """Get lifetime statistics for this member (from user's tracking perspective)"""
        total_transactions = len([mt for mt in self.transactions if mt.transaction.transaction_type == 'expense'])
        total_contribution = 0
        
        for mt in self.transactions:
            transaction = mt.transaction
            if transaction.transaction_type == 'expense':
                cost_per_person = float(transaction.amount) / len(transaction.members)
                total_contribution += cost_per_person
        
        return {
            'total_transactions': total_transactions,
            'total_contribution': total_contribution,
            'average_per_transaction': total_contribution / total_transactions if total_transactions > 0 else 0
        }

    def to_dict(self):
        """Convert member to dictionary for user's family management interface"""
        stats = self.get_lifetime_stats()
        return {
            'member_id': self.member_id,
            'user_id': self.user_id,
            'name': self.name,
            'relationship': self.relationship,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'total_contribution': stats['total_contribution'],
            'total_transactions': stats['total_transactions'],
            'is_data_entity': True,  # Clarifies this is not a user account
            'managed_by_user': True  # Only the user can modify this data
        }

    def __repr__(self):
        return f'Member {self.name} (managed by User {self.user_id})'

#Category set to nullable in case an user delete a category so the data is not automaticcaly deleted
#!!!check model in budget class- this model in transaction has the problem that users are associated with every transaction creating problems in cost splitting and etc
class Transaction(db.Model):
    __tablename__ = 'transactions'
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)
    amount = db.Column(db.Numeric(8, 2), nullable=False)
    transaction_type = db.Column(db.Enum('income', 'expense', name='transaction_type_enum'), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)  # for analytics
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now()) # for user behavior, monitoring for marketing(peak usage time), future features

    # Relationships
    members = db.relationship('MembersTransaction', back_populates='transaction', cascade='all, delete-orphan')


    # Helper methods for transaction categorization from USER's perspective
    # Members are data entities - only the User creates transactions and assigns members for tracking
    def get_associated_members(self):
        """Get all family members the User assigned to this transaction for cost tracking"""
        return [mt.member for mt in self.members] 

    def is_personal_transaction(self):
        """Check if this is a personal expense (User only) vs family expense (User + members)"""
        return len(self.members) == 0
    
    def is_family_expense(self):
        """Check if this is a family/shared expense (has assigned members)"""
        return len(self.members) > 0
    
    def get_cost_per_person(self):
        """Calculate cost per person for family expenses (User's calculation)"""
        if self.is_personal_transaction():
            return float(self.amount)  # User pays full amount
        else:
            # Split equally among all participants (User + assigned members)
            total_people = len(self.members) + 1  # +1 for the User
            return float(self.amount) / total_people
    
    def get_user_share(self):
        """Get the User's portion of this expense"""
        return self.get_cost_per_person()
    
    def get_members_total_share(self):
        """Get combined share of all assigned members (for tracking purposes)"""
        if self.is_personal_transaction():
            return 0
        else:
            cost_per_person = self.get_cost_per_person()
            return cost_per_person * len(self.members)

    # Data serialization from User's management perspective
    def to_dict(self):
        """Convert transaction to dictionary - shows User's expense tracking data"""
        return {
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'type': self.transaction_type,
            'category': self.category.category_name if self.category else 'Uncategorized',
            'date': self.transaction_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'assigned_members': [member.name for member in self.get_associated_members()],
            'is_personal': self.is_personal_transaction(),
            'is_family_expense': self.is_family_expense(),
            'user_share': self.get_user_share(),
            'members_total_share': self.get_members_total_share(),
            'cost_per_person': self.get_cost_per_person(),
            'expense_type': 'Personal' if self.is_personal_transaction() else 'Family/Shared'
        }

    def __repr__(self):
        return f'Transaction {self.transaction_id}: ${self.amount} ({self.transaction_type})'

class MembersTransaction(db.Model):
    __tablename__ = 'members_transaction'
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.transaction_id', ondelete='CASCADE'), primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'), primary_key=True) # cascade will be triggered by sqlAlchemy when the parent will be deleted in the database

    # Relationships
    transaction = db.relationship('Transaction', back_populates='members')
    member = db.relationship('Member', back_populates='transactions')

    def to_dict(self):
        """Convert member transaction to dictionary"""
        return {
            'transaction_id': self.transaction_id,
            'member_id': self.member_id,
            'member_name': self.member.name if self.member else None
        }

    def __repr__(self):
        return f'MembersTransaction {self.member_id}-{self.transaction_id}'

## Decide if using simple version like in transaction but with the problem of not being able to have 
# a transaction associated just with a member or more advanced like in budget
# with clear ownership separations and flexible combinations
class Budget(db.Model):
    __tablename__ = 'budgets'
    
    budget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    budget_amount = db.Column(db.Numeric(10, 2), nullable=False)
    budget_period = db.Column(db.String(20), nullable=False, default='monthly')  # 'weekly', 'monthly', 'yearly'
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Whether budget is currently active
    alert_threshold = db.Column(db.Numeric(5, 2), nullable=False, default=80.0)  # Alert when % of budget is reached (default 80%)
    notifications_enabled = db.Column(db.Boolean, nullable=False, default=True)  # Enable/disable budget alerts
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Foreign keys - budget can be for user OR member, and for specific category OR total expenses
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)  # SET NULL since categories are ENUM-constrained
    
    # Relationships
    category = db.relationship('Category', backref='budgets')
    
    def is_user_budget(self):
        """Check if this is a user budget (not member budget)"""
        return self.user_id is not None and self.member_id is None
    
    def is_member_budget(self):
        """Check if this is a member budget"""
        return self.member_id is not None
    
    def is_category_budget(self):
        """Check if this is a category-specific budget"""
        return self.category_id is not None
    
    def is_total_budget(self):
        """Check if this is a total expenses budget (all categories)"""
        return self.category_id is None
    
    def pause(self):
        """Pause/deactivate this budget"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def unpause(self):
        """Unpause/activate this budget"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def is_paused(self):
        """Check if this budget is currently paused"""
        return not self.is_active
    
    def should_alert(self, current_spending):
        """Check if an alert should be triggered based on current spending"""
        if not self.notifications_enabled or self.budget_amount <= 0:
            return False
        
        percentage_used = (current_spending / float(self.budget_amount)) * 100
        return percentage_used >= float(self.alert_threshold)
    
    def get_alert_status(self, current_spending):
        """Get detailed alert status information"""
        if self.budget_amount <= 0:
            return {
                'should_alert': False,
                'percentage_used': 0,
                'amount_remaining': 0,
                'status': 'invalid_budget'
            }
        
        percentage_used = (current_spending / float(self.budget_amount)) * 100
        amount_remaining = float(self.budget_amount) - current_spending
        
        if percentage_used >= 100:
            status = 'over_budget'
        elif percentage_used >= float(self.alert_threshold):
            status = 'alert_threshold_reached'
        elif percentage_used >= (float(self.alert_threshold) - 10):  # Within 10% of threshold
            status = 'approaching_threshold'
        else:
            status = 'within_budget'
        
        return {
            'should_alert': self.should_alert(current_spending),
            'percentage_used': round(percentage_used, 2),
            'amount_remaining': round(amount_remaining, 2),
            'alert_threshold': float(self.alert_threshold),
            'status': status,
            'notifications_enabled': self.notifications_enabled
        }
    
    
    def to_dict(self):
        """Convert budget to dictionary"""
        # Get category name safely
        category_name = 'Total Expenses'  
        if self.category_id and self.category:
            category_name = self.category.category_name
        
        return {
            'budget_id': self.budget_id,
            'budget_amount': float(self.budget_amount) if self.budget_amount else 0,
            'budget_period': self.budget_period,
            'is_active': self.is_active,
            'alert_threshold': float(self.alert_threshold) if self.alert_threshold else 80.0,
            'notifications_enabled': self.notifications_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'member_id': self.member_id,
            'category_id': self.category_id,
            'category_name': category_name,
            'owner_name': 'Budget Owner',  
            'owner_type': 'user' if self.is_user_budget() else 'member',
            'budget_type': 'category' if self.is_category_budget() else 'total'
        }
    
    def __repr__(self):
        owner = "Budget Owner"  
        category = self.category.category_name if self.category else 'Total Expenses'
        return f'Budget {owner} - {category}: ${self.budget_amount}'
