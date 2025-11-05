"""
Service Layer Tests for Smart Expenses Tracker
Tests all service classes and business logic
"""

import pytest
import time
from decimal import Decimal
from datetime import datetime, timedelta
from app import db
from app.models import User, Transaction, Category, Member, Budget
from app.services import (
    UserService, TransactionService, SimpleAnalyticsService,
    CategoryService, BudgetService, MemberService
)
from test.conftest import TestDataFactory, PerformanceTestUtils

class TestUserService:
    """Test UserService functionality"""
    
    def test_get_user_by_id(self, app, test_user):
        """Test getting user by ID"""
        with app.app_context():
            found_user = UserService.get_user_by_id(test_user.user_id)
            assert found_user is not None
            assert found_user.user_id == test_user.user_id
            assert found_user.email == test_user.email
    
    def test_get_user_by_email(self, app, test_user):
        """Test getting user by email"""
        with app.app_context():
            found_user = UserService.get_user_by_email(test_user.email)
            assert found_user is not None
            assert found_user.user_id == test_user.user_id
    
    def test_create_user(self, app):
        """Test user creation through service"""
        with app.app_context():
            unique_email = f"service_{int(time.time())}@example.com"
            user = UserService.create_user(
                username="Service Test User",
                email=unique_email,
                password_hash="hashed_password"
            )
            
            assert user.user_id is not None
            assert user.user_name == "Service Test User"
            assert user.email == unique_email
    
    def test_add_member_to_user(self, app, test_user):
        """Test adding member through service"""
        with app.app_context():
            member = UserService.add_member_to_user(
                test_user, "Service Member", "sibling"
            )
            
            assert member.member_id is not None
            assert member.user_id == test_user.user_id
            assert member.name == "Service Member"
            assert member.relationship == "sibling"


class TestTransactionService:
    """Test TransactionService functionality"""
    
    def test_create_transaction(self, app, test_user, test_category):
        """Test basic transaction creation"""
        with app.app_context():
            transaction = TransactionService.create_transaction(
                user_id=test_user.user_id,
                amount=Decimal('75.50'),
                category_id=test_category.category_id,
                transaction_type='expense'
            )
            
            assert transaction.transaction_id is not None
            assert transaction.amount == Decimal('75.50')
            assert transaction.user_participates == True  # Default
    
    def test_add_personal_transaction(self, app, test_user, test_category):
        """Test adding personal transaction"""
        with app.app_context():
            transaction = TransactionService.add_personal_transaction(
                user=test_user,
                amount=Decimal('100.00'),
                transaction_type='expense',
                category_id=test_category.category_id
            )
            
            assert transaction.is_personal_transaction() == True
            assert transaction.user_participates == True
            assert len(transaction.members) == 0
    
    def test_add_shared_transaction(self, app, test_user, test_category, test_member):
        """Test adding shared transaction with members"""
        with app.app_context():
            transaction = TransactionService.add_shared_transaction(
                user=test_user,
                amount=Decimal('150.00'),
                transaction_type='expense',
                category_id=test_category.category_id,
                member_ids=[test_member.member_id],
                user_participates=True
            )
            
            assert transaction.is_family_expense() == True
            assert transaction.user_participates == True
            assert len(transaction.members) == 1
            assert transaction.get_cost_per_person() == 75.00  # 150 / 2
    
    def test_add_member_transaction(self, app, test_user, test_category, test_member):
        """Test adding member-only transaction"""
        with app.app_context():
            transaction = TransactionService.add_member_transaction(
                user=test_user,
                member_id=test_member.member_id,
                amount=Decimal('50.00'),
                transaction_type='expense',
                category_id=test_category.category_id
            )
            
            assert transaction.is_members_only_expense() == True
            assert transaction.user_participates == False
            assert transaction.get_user_share() == 0.00
            assert transaction.get_members_total_share() == 50.00
    
    def test_get_user_transactions(self, app, test_user, test_category):
        """Test getting user transactions"""
        with app.app_context():
            # Create multiple transactions
            for i in range(3):
                TransactionService.add_personal_transaction(
                    test_user, Decimal('10.00'), 'expense', test_category.category_id
                )
            
            transactions = TransactionService.get_user_transactions(test_user.user_id)
            assert len(transactions) >= 3
            
            # Should be ordered by date descending
            if len(transactions) > 1:
                assert transactions[0].transaction_date >= transactions[1].transaction_date
    
    def test_get_recent_transactions(self, app, test_user, test_category):
        """Test getting recent transactions with limit"""
        with app.app_context():
            # Create 5 transactions
            for i in range(5):
                TransactionService.add_personal_transaction(
                    test_user, Decimal(f'{i*10}.00'), 'expense', test_category.category_id
                )
            
            recent = TransactionService.get_recent_transactions(test_user.user_id, limit=3)
            assert len(recent) == 3
    
    def test_delete_transaction(self, app, test_user, test_category):
        """Test transaction deletion"""
        with app.app_context():
            transaction = TransactionService.add_personal_transaction(
                test_user, Decimal('25.00'), 'expense', test_category.category_id
            )
            transaction_id = transaction.transaction_id
            
            # Delete transaction
            result = TransactionService.delete_transaction(transaction_id)
            assert result == True
            
            # Verify deletion
            deleted_tx = Transaction.query.get(transaction_id)
            assert deleted_tx is None


class TestSimpleAnalyticsService:
    """Test SimpleAnalyticsService functionality"""
    
    def test_get_total_income(self, app, test_user, test_category):
        """Test total income calculation"""
        with app.app_context():
            # Add income transactions
            TransactionService.add_personal_transaction(
                test_user, Decimal('1000.00'), 'income', test_category.category_id
            )
            TransactionService.add_personal_transaction(
                test_user, Decimal('500.00'), 'income', test_category.category_id
            )
            
            total_income = SimpleAnalyticsService.get_total_income(test_user.user_id)
            assert total_income == 1500.00
    
    def test_get_total_expenses(self, app, test_user, test_category):
        """Test total expenses calculation"""
        with app.app_context():
            # Add expense transactions
            TransactionService.add_personal_transaction(
                test_user, Decimal('200.00'), 'expense', test_category.category_id
            )
            TransactionService.add_personal_transaction(
                test_user, Decimal('150.00'), 'expense', test_category.category_id
            )
            
            total_expenses = SimpleAnalyticsService.get_total_expenses(test_user.user_id)
            assert total_expenses == 350.00
    
    def test_get_balance(self, app, test_user, test_category):
        """Test balance calculation"""
        with app.app_context():
            # Add income and expenses
            TransactionService.add_personal_transaction(
                test_user, Decimal('1000.00'), 'income', test_category.category_id
            )
            TransactionService.add_personal_transaction(
                test_user, Decimal('300.00'), 'expense', test_category.category_id
            )
            
            balance = SimpleAnalyticsService.get_balance(test_user.user_id)
            assert balance == 700.00
    
    def test_get_monthly_totals(self, app, test_user, test_category):
        """Test monthly totals calculation"""
        with app.app_context():
            # Add transactions for current month
            now = datetime.now()
            
            TransactionService.add_personal_transaction(
                test_user, Decimal('800.00'), 'income', test_category.category_id
            )
            TransactionService.add_personal_transaction(
                test_user, Decimal('200.00'), 'expense', test_category.category_id
            )
            
            monthly = SimpleAnalyticsService.get_monthly_totals(
                test_user.user_id, now.year, now.month
            )
            
            assert 'income' in monthly
            assert 'expenses' in monthly
            assert 'balance' in monthly
            assert 'transaction_count' in monthly
            assert monthly['income'] >= 800.00
            assert monthly['expenses'] >= 200.00
    
    def test_get_spending_by_category(self, app, test_user):
        """Test spending breakdown by category"""
        with app.app_context():
            # Get multiple categories
            food_cat = Category.query.filter_by(category_name='Food').first()
            transport_cat = Category.query.filter_by(category_name='Transport').first()
            
            if food_cat and transport_cat:
                # Add transactions in different categories
                TransactionService.add_personal_transaction(
                    test_user, Decimal('100.00'), 'expense', food_cat.category_id
                )
                TransactionService.add_personal_transaction(
                    test_user, Decimal('50.00'), 'expense', transport_cat.category_id
                )
                
                spending = SimpleAnalyticsService.get_spending_by_category(test_user.user_id)
                
                assert 'Food' in spending
                assert 'Transport' in spending
                assert spending['Food'] >= 100.00
                assert spending['Transport'] >= 50.00


class TestCategoryService:
    """Test CategoryService functionality"""
    
    def test_get_all_categories(self, app):
        """Test getting all categories"""
        with app.app_context():
            categories = CategoryService.get_all_categories()
            assert len(categories) > 0
            
            # Should include system categories
            category_names = [cat.category_name for cat in categories]
            assert 'Food' in category_names
    
    def test_get_system_categories(self, app):
        """Test getting system categories only"""
        with app.app_context():
            system_cats = CategoryService.get_system_categories()
            
            for cat in system_cats:
                assert cat.user_id is None  # System categories have no user
    
    def test_initialize_system_categories(self, app):
        """Test system category initialization"""
        with app.app_context():
            # Clear existing categories
            Category.query.delete()
            db.session.commit()
            
            # Initialize system categories
            created_count = CategoryService.initialize_system_categories()
            assert created_count > 0
            
            # Verify categories exist
            categories = CategoryService.get_system_categories()
            assert len(categories) == created_count


class TestBudgetService:
    """Test BudgetService functionality"""
    
    def test_create_simple_budget(self, app, test_user, test_category):
        """Test budget creation"""
        with app.app_context():
            budget = BudgetService.create_simple_budget(
                test_user.user_id,
                test_category.category_id,
                Decimal('500.00'),
                'monthly'
            )
            
            assert budget.budget_id is not None
            assert budget.user_id == test_user.user_id
            assert budget.budget_amount == Decimal('500.00')
            assert budget.is_active == True
    
    def test_get_user_budgets(self, app, test_user, test_category):
        """Test getting user budgets"""
        with app.app_context():
            # Create budgets
            BudgetService.create_simple_budget(
                test_user.user_id, test_category.category_id, Decimal('300.00')
            )
            BudgetService.create_simple_budget(
                test_user.user_id, None, Decimal('1000.00')  # Total budget
            )
            
            budgets = BudgetService.get_user_budgets(test_user.user_id)
            assert len(budgets) >= 2
            
            # All should be active
            for budget in budgets:
                assert budget.is_active == True
    
    def test_check_budget_status(self, app, test_user, test_category):
        """Test budget status checking"""
        with app.app_context():
            # Create budget
            budget = BudgetService.create_simple_budget(
                test_user.user_id, test_category.category_id, Decimal('200.00')
            )
            
            # Add some spending
            TransactionService.add_personal_transaction(
                test_user, Decimal('150.00'), 'expense', test_category.category_id
            )
            
            status = BudgetService.check_budget_status(
                test_user.user_id, test_category.category_id
            )
            
            assert 'budget_amount' in status
            assert 'spent' in status
            assert 'remaining' in status
            assert 'is_over_budget' in status
            assert 'percentage_used' in status
            
            assert status['spent'] >= 150.00
            assert status['percentage_used'] >= 75.0


class TestMemberService:
    """Test MemberService functionality"""
    
    def test_get_user_members(self, app, test_user, test_member):
        """Test getting user members"""
        with app.app_context():
            members = MemberService.get_user_members(test_user.user_id)
            assert len(members) >= 1
            
            member_names = [member.name for member in members]
            assert test_member.name in member_names
    
    def test_get_member_by_id(self, app, test_member):
        """Test getting member by ID"""
        with app.app_context():
            found_member = MemberService.get_member_by_id(test_member.member_id)
            assert found_member is not None
            assert found_member.member_id == test_member.member_id


class TestServicePerformance:
    """Test service performance and optimization"""
    
    def test_transaction_query_performance(self, app, test_user, test_category):
        """Test transaction query performance"""
        with app.app_context():
            # Create multiple transactions
            for i in range(50):
                TransactionService.add_personal_transaction(
                    test_user, Decimal('10.00'), 'expense', test_category.category_id
                )
            
            # Test query performance
            result, execution_time = PerformanceTestUtils.time_database_operation(
                TransactionService.get_user_transactions, test_user.user_id
            )
            
            PerformanceTestUtils.assert_query_performance(execution_time, 2.0)
            assert len(result) >= 50
    
    def test_analytics_performance(self, app, test_user, test_category):
        """Test analytics calculation performance"""
        with app.app_context():
            # Create transactions for performance test
            for i in range(100):
                tx_type = 'income' if i % 3 == 0 else 'expense'
                TransactionService.add_personal_transaction(
                    test_user, Decimal('25.00'), tx_type, test_category.category_id
                )
            
            # Test balance calculation performance
            result, execution_time = PerformanceTestUtils.time_database_operation(
                SimpleAnalyticsService.get_balance, test_user.user_id
            )
            
            PerformanceTestUtils.assert_query_performance(execution_time, 1.0)
            assert isinstance(result, (int, float))


class TestServiceIntegration:
    """Test service integration and workflows"""
    
    def test_complete_user_setup_workflow(self, app):
        """Test complete user setup through services"""
        with app.app_context():
            # Create user
            user = UserService.create_user(
                "Integration User", "integration@example.com", "hashed_pass"
            )
            
            # Add member
            member = UserService.add_member_to_user(user, "Child", "child")
            
            # Get category
            category = Category.query.filter_by(category_name='Food').first()
            
            # Create budget
            budget = BudgetService.create_simple_budget(
                user.user_id, category.category_id, Decimal('500.00')
            )
            
            # Add transactions
            TransactionService.add_personal_transaction(
                user, Decimal('100.00'), 'expense', category.category_id
            )
            TransactionService.add_shared_transaction(
                user, Decimal('200.00'), 'expense', category.category_id,
                [member.member_id], user_participates=True
            )
            
            # Verify complete setup
            assert user.user_id is not None
            assert len(MemberService.get_user_members(user.user_id)) == 1
            assert len(BudgetService.get_user_budgets(user.user_id)) == 1
            assert len(TransactionService.get_user_transactions(user.user_id)) == 2
            
            # Test analytics
            balance = SimpleAnalyticsService.get_balance(user.user_id)
            expenses = SimpleAnalyticsService.get_total_expenses(user.user_id)
            assert expenses >= 300.00  # 100 + 200
            assert balance == -expenses  # No income added
    
    def test_transaction_splitting_workflow(self, app, test_user, test_category):
        """Test complex transaction splitting scenarios"""
        with app.app_context():
            # Create multiple members
            spouse = UserService.add_member_to_user(test_user, "Spouse", "spouse")
            child1 = UserService.add_member_to_user(test_user, "Child 1", "child")
            child2 = UserService.add_member_to_user(test_user, "Child 2", "child")
            
            # Test different splitting scenarios
            scenarios = [
                # (amount, member_ids, user_participates, expected_user_share)
                (Decimal('100.00'), [], True, 100.00),  # Personal
                (Decimal('120.00'), [spouse.member_id], True, 60.00),  # User + Spouse
                (Decimal('200.00'), [child1.member_id, child2.member_id], False, 0.00),  # Kids only
                (Decimal('300.00'), [spouse.member_id, child1.member_id], True, 100.00),  # All 3
            ]
            
            for amount, member_ids, user_participates, expected_share in scenarios:
                if member_ids:
                    tx = TransactionService.add_shared_transaction(
                        test_user, amount, 'expense', test_category.category_id,
                        member_ids, user_participates
                    )
                else:
                    tx = TransactionService.add_personal_transaction(
                        test_user, amount, 'expense', test_category.category_id
                    )
                
                assert abs(tx.get_user_share() - float(expected_share)) < 0.01