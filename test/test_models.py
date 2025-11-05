"""
Model Tests for Smart Expenses Tracker
Tests all models: User, Transaction, Category, Member, Budget
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app import db
from app.models import User, Transaction, Category, Member, Budget, MembersTransaction
from test.conftest import TestDataFactory, CustomAssertions

class TestUserModel:
    """Test the User model"""
    
    def test_user_creation(self, app):
        """Test basic user creation"""
        with app.app_context():
            user = TestDataFactory.create_test_user("creation")
            db.session.add(user)
            db.session.commit()
            
            assert user.user_id is not None
            assert user.user_name == "Test User creation"
            assert user.email.endswith("@example.com")
            assert user.created_at is not None
            assert user.is_admin == False  # Default value
    
    def test_password_hashing(self, app):
        """Test password hashing and verification"""
        with app.app_context():
            user = TestDataFactory.create_test_user("password")
            
            # Test password setting
            user.set_password("mypassword123")
            assert user.password_hash is not None
            assert user.password_hash != "mypassword123"  # Should be hashed
            
            # Test password verification
            assert user.check_password("mypassword123") == True
            assert user.check_password("wrongpassword") == False
    
    def test_flask_login_integration(self, app):
        """Test Flask-Login integration"""
        with app.app_context():
            user = TestDataFactory.create_test_user("login")
            db.session.add(user)
            db.session.commit()
            
            # Test Flask-Login methods
            assert user.is_authenticated == True
            assert user.is_active == True
            assert user.is_anonymous == False
            assert user.get_id() == str(user.user_id)
    
    def test_admin_functionality(self, app):
        """Test admin user functionality"""
        with app.app_context():
            # Regular user
            user = TestDataFactory.create_test_user("regular")
            db.session.add(user)
            db.session.commit()
            assert user.is_administrator() == False
            
            # Admin user
            admin = TestDataFactory.create_test_user("admin")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            assert admin.is_administrator() == True
    
    def test_user_relationships(self, app):
        """Test user relationships with other models"""
        with app.app_context():
            # Create a fresh user for this test
            user = TestDataFactory.create_test_user("relationships")
            db.session.add(user)
            db.session.commit()
            
            # Test that relationships are properly set up
            assert hasattr(user, 'members')
            assert hasattr(user, 'transactions')
            assert hasattr(user, 'categories')
            assert hasattr(user, 'budgets')
            
            # Test relationships are initially empty
            assert len(user.members) == 0
            assert len(user.transactions) == 0
            assert len(user.budgets) == 0
    
    def test_user_serialization(self, app):
        """Test user to_dict method"""
        with app.app_context():
            # Create a fresh user for this test
            user = TestDataFactory.create_test_user("serialization")
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            
            required_fields = ['user_id', 'user_name', 'email', 'created_at']
            for field in required_fields:
                assert field in user_dict
            
            # Ensure password is not exposed
            assert 'password_hash' not in user_dict
            assert 'password' not in user_dict


class TestCategoryModel:
    """Test the Category model"""
    
    def test_system_category_creation(self, app):
        """Test system category creation"""
        with app.app_context():
            category = Category(category_name='Transport', user_id=None)
            db.session.add(category)
            db.session.commit()
            
            assert category.category_id is not None
            assert category.category_name == 'Transport'
            assert category.user_id is None
    
    def test_category_serialization(self, app, test_category):
        """Test category to_dict method"""
        with app.app_context():
            category_dict = test_category.to_dict()
            
            assert 'category_id' in category_dict
            assert 'category_name' in category_dict
            assert 'is_system_category' in category_dict
            assert category_dict['is_system_category'] == True  # test_category is system category


class TestMemberModel:
    """Test the Member model"""
    
    def test_member_creation(self, app, test_user):
        """Test member creation"""
        with app.app_context():
            member = Member(
                user_id=test_user.user_id,
                name="Test Child",
                relationship="child"
            )
            db.session.add(member)
            db.session.commit()
            
            assert member.member_id is not None
            assert member.name == "Test Child"
            assert member.relationship == "child"
            assert member.joined_at is not None
    
    def test_member_relationships(self, app, test_member):
        """Test member relationships"""
        with app.app_context():
            assert test_member.user is not None
            assert hasattr(test_member, 'transactions')
            assert len(test_member.transactions) == 0
    
    def test_member_statistics(self, app, test_member):
        """Test member statistics methods"""
        with app.app_context():
            # Test lifetime stats
            stats = test_member.get_lifetime_stats()
            
            assert 'total_transactions' in stats
            assert 'total_contribution' in stats
            assert 'average_per_transaction' in stats
            assert stats['total_transactions'] == 0  # No transactions yet
    
    def test_member_serialization(self, app, test_member):
        """Test member to_dict method"""
        with app.app_context():
            member_dict = test_member.to_dict()
            
            required_fields = ['member_id', 'user_id', 'name', 'relationship', 'joined_at', 'is_data_entity']
            for field in required_fields:
                assert field in member_dict
            
            assert member_dict['is_data_entity'] == True


class TestTransactionModel:
    """Test the Transaction model"""
    
    def test_transaction_creation(self, app, test_user, test_category):
        """Test basic transaction creation"""
        with app.app_context():
            transaction = TestDataFactory.create_test_transaction(
                test_user.user_id, test_category.category_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert transaction.transaction_id is not None
            assert transaction.user_id == test_user.user_id
            assert transaction.amount == Decimal('50.00')
            assert transaction.transaction_type == 'expense'
            assert transaction.user_participates == True  # Default value
    
    def test_personal_transaction(self, app, test_user, test_category):
        """Test personal transaction (no members)"""
        with app.app_context():
            transaction = TestDataFactory.create_test_transaction(
                test_user.user_id, test_category.category_id, 100.00
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert transaction.is_personal_transaction() == True
            assert transaction.is_family_expense() == False
            assert transaction.get_cost_per_person() == 100.00
            assert transaction.get_user_share() == 100.00
            assert transaction.get_members_total_share() == 0.00
    
    def test_shared_transaction_with_user_participation(self, app, test_user, test_category, test_member):
        """Test shared transaction where user participates"""
        with app.app_context():
            transaction = TestDataFactory.create_test_transaction(
                test_user.user_id, test_category.category_id, 120.00
            )
            transaction.user_participates = True
            db.session.add(transaction)
            db.session.commit()
            
            # Add member to transaction
            member_tx = MembersTransaction(
                transaction_id=transaction.transaction_id,
                member_id=test_member.member_id
            )
            db.session.add(member_tx)
            db.session.commit()
            
            assert transaction.is_family_expense() == True
            assert transaction.is_user_participating() == True
            assert transaction.get_cost_per_person() == 60.00  # 120 / 2 (user + member)
            assert transaction.get_user_share() == 60.00
            assert transaction.get_members_total_share() == 60.00
            assert transaction.get_user_net_expense() == 60.00  # 120 - 60
    
    def test_members_only_transaction(self, app, test_user, test_category, test_member):
        """Test transaction where user pays but doesn't participate"""
        with app.app_context():
            transaction = TestDataFactory.create_test_transaction(
                test_user.user_id, test_category.category_id, 80.00
            )
            transaction.user_participates = False  # User doesn't participate
            db.session.add(transaction)
            db.session.commit()
            
            # Add member to transaction
            member_tx = MembersTransaction(
                transaction_id=transaction.transaction_id,
                member_id=test_member.member_id
            )
            db.session.add(member_tx)
            db.session.commit()
            
            assert transaction.is_members_only_expense() == True
            assert transaction.is_user_participating() == False
            assert transaction.get_cost_per_person() == 80.00  # 80 / 1 (only member)
            assert transaction.get_user_share() == 0.00  # User doesn't participate
            assert transaction.get_members_total_share() == 80.00
            assert transaction.get_user_net_expense() == 0.00  # 80 - 80
    
    def test_transaction_expense_type_descriptions(self, app, test_user, test_category):
        """Test expense type descriptions"""
        with app.app_context():
            # Personal transaction
            personal_tx = TestDataFactory.create_test_transaction(
                test_user.user_id, test_category.category_id
            )
            assert personal_tx.get_expense_type_description() == 'Personal'
    
    def test_transaction_serialization(self, app, test_user, test_category):
        """Test transaction to_dict method"""
        with app.app_context():
            transaction = TestDataFactory.create_test_transaction(
                test_user.user_id, test_category.category_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            tx_dict = transaction.to_dict()
            
            required_fields = [
                'transaction_id', 'amount', 'type', 'category', 'date',
                'is_personal', 'user_participates', 'user_share',
                'cost_per_person', 'expense_type'
            ]
            for field in required_fields:
                assert field in tx_dict


class TestBudgetModel:
    """Test the Budget model"""
    
    def test_budget_creation(self, app, test_user, test_category):
        """Test basic budget creation"""
        with app.app_context():
            budget = TestDataFactory.create_test_budget(
                test_user.user_id, test_category.category_id
            )
            db.session.add(budget)
            db.session.commit()
            
            assert budget.budget_id is not None
            assert budget.user_id == test_user.user_id
            assert budget.budget_amount == Decimal('500.00')
            assert budget.is_active == True
            assert budget.alert_threshold == Decimal('80.0')
    
    def test_budget_ownership_validation(self, app, test_user):
        """Test budget ownership validation"""
        with app.app_context():
            # Valid user budget
            user_budget = TestDataFactory.create_test_budget(test_user.user_id)
            is_valid, message = user_budget.validate_budget_ownership()
            assert is_valid == True
            
            # Invalid budget (no user or member)
            invalid_budget = Budget(budget_amount=Decimal('100.00'))
            is_valid, message = invalid_budget.validate_budget_ownership()
            assert is_valid == False
            assert "must belong to either" in message
    
    def test_budget_alert_functionality(self, app, test_user):
        """Test budget alert system"""
        with app.app_context():
            budget = TestDataFactory.create_test_budget(test_user.user_id, amount=100.00)
            budget.alert_threshold = Decimal('80.0')
            
            # Test alert conditions
            assert budget.should_alert(50.0) == False  # 50% - no alert
            assert budget.should_alert(80.0) == True   # 80% - alert
            assert budget.should_alert(90.0) == True   # 90% - alert
            
            # Test alert status
            status = budget.get_alert_status(85.0)
            assert status['should_alert'] == True
            assert status['percentage_used'] == 85.0
            assert status['amount_remaining'] == 15.0
            assert status['status'] == 'alert_threshold_reached'
    
    def test_budget_pause_functionality(self, app, test_user):
        """Test budget pause/unpause"""
        with app.app_context():
            budget = TestDataFactory.create_test_budget(test_user.user_id)
            
            # Test pause
            budget.pause()
            assert budget.is_paused() == True
            assert budget.is_active == False
            
            # Test unpause
            budget.unpause()
            assert budget.is_paused() == False
            assert budget.is_active == True
    
    def test_budget_serialization(self, app, test_user, test_category):
        """Test budget to_dict method"""
        with app.app_context():
            budget = TestDataFactory.create_test_budget(
                test_user.user_id, test_category.category_id
            )
            db.session.add(budget)
            db.session.commit()
            
            budget_dict = budget.to_dict()
            
            required_fields = [
                'budget_id', 'budget_amount', 'budget_period', 'is_active',
                'owner_type', 'budget_type', 'category_name'
            ]
            for field in required_fields:
                assert field in budget_dict


class TestModelRelationships:
    """Test relationships between models"""
    
    def test_user_cascade_deletion(self, app):
        """Test that user deletion cascades properly"""
        with app.app_context():
            # Create user with related data
            user = TestDataFactory.create_test_user("cascade")
            db.session.add(user)
            db.session.commit()
            
            # Create related objects
            member = Member(user_id=user.user_id, name="Test", relationship="child")
            category = Category.query.filter_by(category_name='Food').first()
            transaction = TestDataFactory.create_test_transaction(user.user_id, category.category_id)
            budget = TestDataFactory.create_test_budget(user.user_id)
            
            db.session.add_all([member, transaction, budget])
            db.session.commit()
            
            # Get IDs for verification
            member_id = member.member_id
            transaction_id = transaction.transaction_id
            budget_id = budget.budget_id
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            # Verify cascade deletion
            assert Member.query.get(member_id) is None
            assert Transaction.query.get(transaction_id) is None
            assert Budget.query.get(budget_id) is None
    
    def test_category_soft_deletion(self, app, test_user):
        """Test that category deletion doesn't cascade to transactions"""
        with app.app_context():
            # Create category and transaction
            category = Category(category_name='Food', user_id=None)
            db.session.add(category)
            db.session.commit()
            
            transaction = TestDataFactory.create_test_transaction(
                test_user.user_id, category.category_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            transaction_id = transaction.transaction_id
            
            # Delete category
            db.session.delete(category)
            db.session.commit()
            
            # Transaction should still exist but with null category_id
            remaining_transaction = Transaction.query.get(transaction_id)
            assert remaining_transaction is not None
            assert remaining_transaction.category_id is None