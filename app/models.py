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

    # Relationships
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

    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.user_name}>'

class Category(db.Model): 
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.Enum('Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other', name='category_enum'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)  

    # Relationships
    transactions = db.relationship('Transaction', backref='category', passive_deletes=True)

    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'user_id': self.user_id,
            'is_system_category': self.user_id is None
        }

    def __repr__(self):
        return f'<Category {self.category_name}>'

class Member(db.Model):
    __tablename__ = 'members'
    member_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    relationship = db.Column(db.String(100), nullable=False)  
    joined_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    transactions = db.relationship('MembersTransaction', back_populates='member', cascade='all, delete-orphan')

    # Simple profile update 
    def to_dict(self):
        """Convert member to dictionary"""
        return {
            'member_id': self.member_id,
            'user_id': self.user_id,
            'name': self.name,
            'relationship': self.relationship,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }

    def __repr__(self):
        return f'<Member {self.name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)
    amount = db.Column(db.Numeric(8, 2), nullable=False)
    transaction_type = db.Column(db.Enum('income', 'expense', name='transaction_type_enum'), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)  
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    members = db.relationship('MembersTransaction', back_populates='transaction', cascade='all, delete-orphan')


    # Helper methods for checking transaction state
    def get_associated_members(self):
        """Get all members associated with this transaction"""
        return [mt.member for mt in self.members]

    def is_personal_transaction(self):
        """Check if this is a personal transaction (no members associated)"""
        return len(self.members) == 0

    # Data serialization 
    def to_dict(self):
        """Convert transaction to dictionary for export"""
        return {
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'type': self.transaction_type,
            'category': self.category.category_name if self.category else 'Uncategorized',
            'date': self.transaction_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'members': [member.name for member in self.get_associated_members()],
            'is_personal': self.is_personal_transaction()
        }

    def __repr__(self):
        return f'<Transaction {self.transaction_id}: ${self.amount} ({self.transaction_type})>'

class MembersTransaction(db.Model):
    __tablename__ = 'members_transaction'
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.transaction_id', ondelete='CASCADE'), primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'), primary_key=True)

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
        return f'<MembersTransaction {self.member_id}-{self.transaction_id}>'


class Budget(db.Model):
    __tablename__ = 'budgets'
    
    budget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    budget_amount = db.Column(db.Numeric(10, 2), nullable=False)
    budget_period = db.Column(db.String(20), nullable=False, default='monthly')  # 'weekly', 'monthly', 'yearly'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Foreign keys - budget can be for user OR member, and for specific category OR total expenses
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='CASCADE'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='budgets')
    member = db.relationship('Member', backref='budgets')
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
    
    def get_owner_name(self):
        """Get the name of the budget owner (user or member)"""
        if self.is_user_budget():
            return self.user.user_name if self.user else 'Unknown User'
        elif self.is_member_budget():
            return self.member.name if self.member else 'Unknown Member'
        return 'Unknown'
    
    def to_dict(self):
        """Convert budget to dictionary"""
        return {
            'budget_id': self.budget_id,
            'budget_amount': float(self.budget_amount) if self.budget_amount else 0,
            'budget_period': self.budget_period,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'member_id': self.member_id,
            'category_id': self.category_id,
            'category_name': self.category.category_name if self.category else 'Total Expenses',
            'owner_name': self.get_owner_name(),
            'owner_type': 'user' if self.is_user_budget() else 'member',
            'budget_type': 'category' if self.is_category_budget() else 'total'
        }
    
    def __repr__(self):
        owner = self.get_owner_name()
        category = self.category.category_name if self.category else 'Total Expenses'
        return f'<Budget {owner} - {category}: ${self.budget_amount}>'
