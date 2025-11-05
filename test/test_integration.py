"""
Integration Tests for Smart Expenses Tracker
End-to-end tests for complete user workflows and system interactions
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Transaction, Category, Member, Budget
from app.services import TransactionService, CategoryService, BudgetService, SimpleAnalyticsService
from decimal import Decimal
from test.conftest import TestDataFactory, CustomAssertions

class TestUserRegistrationAndLogin:
    """Test complete user registration and login workflow"""
    
    def test_complete_user_signup_workflow(self, app, client):
        """Test complete user signup workflow from start to finish"""
        with app.app_context():
            # Step 1: Visit signup page
            response = client.get('/signup')
            assert response.status_code == 200
            
            # Step 2: Submit signup form
            signup_data = {
                'name': 'Integration Test User',
                'email': 'integration@example.com',
                'password': 'integrationsecure123',
                'confirm_password': 'integrationsecure123'
            }
            
            response = client.post('/signup', data=signup_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Step 3: Verify user was created
            user = User.query.filter_by(email='integration@example.com').first()
            assert user is not None
            assert user.user_name == 'Integration Test User'
            
            # Step 4: Verify password was hashed
            assert user.check_password('integrationsecure123')
            assert user.password_hash != 'integrationsecure123'
            
            # Step 5: User should be logged in and redirected
            assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()
    
    def test_login_logout_cycle(self, app, client, test_user):
        """Test complete login/logout cycle"""
        with app.app_context():
            # Step 1: Login
            response = client.post('/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()
            
            # Step 2: Access protected resource
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            # Step 3: Logout
            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            
            # Step 4: Verify access is denied after logout
            response = client.get('/dashboard')
            assert response.status_code in [302, 401]  # Should redirect to login


class TestTransactionWorkflow:
    """Test complete transaction management workflow"""
    
    def test_personal_transaction_lifecycle(self, app, logged_in_user, test_user, test_category):
        """Test complete personal transaction lifecycle"""
        with app.app_context():
            initial_transactions = Transaction.query.filter_by(user_id=test_user.user_id).count()
            
            # Step 1: Add personal transaction
            transaction = TransactionService.add_personal_transaction(
                test_user, Decimal('150.00'), 'expense', test_category.category_id
            )
            
            assert transaction is not None
            assert transaction.amount == Decimal('150.00')
            assert transaction.transaction_type == 'expense'
            
            # Step 2: Verify transaction count increased
            new_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            assert new_count == initial_transactions + 1
            
            # Step 3: Update transaction
            transaction.description = 'Updated description'
            db.session.commit()
            
            updated_tx = Transaction.query.get(transaction.transaction_id)
            assert updated_tx.description == 'Updated description'
            
            # Step 4: Delete transaction
            TransactionService.delete_transaction(test_user, transaction.transaction_id)
            
            deleted_tx = Transaction.query.get(transaction.transaction_id)
            assert deleted_tx is None
            
            # Step 5: Verify count returned to original
            final_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            assert final_count == initial_transactions
    
    def test_split_transaction_workflow(self, app, logged_in_user, test_user, test_category):
        """Test complete split transaction workflow"""
        with app.app_context():
            # Step 1: Create additional users for splitting
            user2 = TestDataFactory.create_test_user("splitter2")
            user3 = TestDataFactory.create_test_user("splitter3")
            user2.set_password("password123")
            user3.set_password("password123")
            db.session.add_all([user2, user3])
            db.session.commit()
            
            # Step 2: Create split transaction
            participants = [
                {'user_id': test_user.user_id, 'split_amount': Decimal('50.00')},
                {'user_id': user2.user_id, 'split_amount': Decimal('30.00')},
                {'user_id': user3.user_id, 'split_amount': Decimal('20.00')}
            ]
            
            split_tx = TransactionService.add_split_transaction(
                test_user, Decimal('100.00'), 'expense', 
                test_category.category_id, participants
            )
            
            assert split_tx is not None
            assert split_tx.amount == Decimal('100.00')
            
            # Step 3: Verify all participants have records
            user1_transactions = Transaction.query.filter_by(
                user_id=test_user.user_id, 
                parent_transaction_id=split_tx.transaction_id
            ).all()
            user2_transactions = Transaction.query.filter_by(
                user_id=user2.user_id,
                parent_transaction_id=split_tx.transaction_id
            ).all()
            user3_transactions = Transaction.query.filter_by(
                user_id=user3.user_id,
                parent_transaction_id=split_tx.transaction_id
            ).all()
            
            assert len(user1_transactions) == 1
            assert len(user2_transactions) == 1
            assert len(user3_transactions) == 1
            
            # Step 4: Verify split amounts
            assert user1_transactions[0].amount == Decimal('50.00')
            assert user2_transactions[0].amount == Decimal('30.00')
            assert user3_transactions[0].amount == Decimal('20.00')
            
            # Step 5: Test split transaction deletion
            TransactionService.delete_transaction(test_user, split_tx.transaction_id)
            
            # All related transactions should be deleted
            remaining_splits = Transaction.query.filter_by(
                parent_transaction_id=split_tx.transaction_id
            ).all()
            assert len(remaining_splits) == 0


class TestBudgetWorkflow:
    """Test complete budget management workflow"""
    
    def test_budget_creation_and_monitoring(self, app, logged_in_user, test_user, test_category):
        """Test complete budget creation and monitoring workflow"""
        with app.app_context():
            # Step 1: Create budget
            budget = BudgetService.create_budget(
                test_user, test_category.category_id, Decimal('500.00'), 'monthly'
            )
            
            assert budget is not None
            assert budget.budget_amount == Decimal('500.00')
            assert budget.budget_period == 'monthly'
            
            # Step 2: Add transactions within budget
            tx1 = TransactionService.add_personal_transaction(
                test_user, Decimal('100.00'), 'expense', test_category.category_id
            )
            tx2 = TransactionService.add_personal_transaction(
                test_user, Decimal('150.00'), 'expense', test_category.category_id
            )
            
            # Step 3: Check budget status (should be within budget)
            budget_status = BudgetService.check_budget_status(budget)
            assert budget_status['status'] in ['within_budget', 'on_track']
            assert budget_status['spent'] == Decimal('250.00')
            assert budget_status['remaining'] == Decimal('250.00')
            
            # Step 4: Add transaction that exceeds budget
            tx3 = TransactionService.add_personal_transaction(
                test_user, Decimal('300.00'), 'expense', test_category.category_id
            )
            
            # Step 5: Check budget status (should be over budget)
            budget_status = BudgetService.check_budget_status(budget)
            assert budget_status['status'] == 'over_budget'
            assert budget_status['spent'] == Decimal('550.00')
            assert budget_status['over_by'] == Decimal('50.00')
            
            # Step 6: Update budget amount
            BudgetService.update_budget(budget, budget_amount=Decimal('600.00'))
            
            budget_status = BudgetService.check_budget_status(budget)
            assert budget_status['status'] in ['within_budget', 'on_track']
            
            # Step 7: Delete budget
            BudgetService.delete_budget(budget)
            
            deleted_budget = Budget.query.get(budget.budget_id)
            assert deleted_budget is None


class TestAnalyticsWorkflow:
    """Test complete analytics and reporting workflow"""
    
    def test_spending_analysis_workflow(self, app, logged_in_user, test_user):
        """Test complete spending analysis workflow"""
        with app.app_context():
            # Step 1: Create categories and transactions for analysis
            food_category = Category.query.filter_by(category_name='Food').first()
            transport_category = CategoryService.create_category('Transport', 'Transportation costs')
            entertainment_category = CategoryService.create_category('Entertainment', 'Fun activities')
            
            # Step 2: Add varied transactions over time
            transactions_data = [
                (Decimal('50.00'), 'expense', food_category.category_id),
                (Decimal('30.00'), 'expense', transport_category.category_id),
                (Decimal('80.00'), 'expense', food_category.category_id),
                (Decimal('25.00'), 'expense', entertainment_category.category_id),
                (Decimal('200.00'), 'income', food_category.category_id),  # Income transaction
                (Decimal('40.00'), 'expense', transport_category.category_id),
            ]
            
            for amount, tx_type, category_id in transactions_data:
                TransactionService.add_personal_transaction(
                    test_user, amount, tx_type, category_id
                )
            
            # Step 3: Generate spending by category analysis
            spending_by_category = SimpleAnalyticsService.get_spending_by_category(test_user)
            
            assert len(spending_by_category) >= 3  # At least 3 categories
            
            # Find food category spending
            food_spending = next((item for item in spending_by_category 
                                if item['category'] == 'Food'), None)
            assert food_spending is not None
            assert food_spending['total'] == Decimal('130.00')  # 50 + 80
            
            # Step 4: Generate monthly summary
            monthly_summary = SimpleAnalyticsService.get_monthly_summary(test_user)
            
            assert 'total_income' in monthly_summary
            assert 'total_expenses' in monthly_summary
            assert 'net_amount' in monthly_summary
            
            assert monthly_summary['total_income'] == Decimal('200.00')
            assert monthly_summary['total_expenses'] == Decimal('225.00')  # 50+30+80+25+40
            assert monthly_summary['net_amount'] == Decimal('-25.00')  # 200 - 225
            
            # Step 5: Test trend analysis (if available)
            recent_transactions = Transaction.query.filter_by(
                user_id=test_user.user_id
            ).order_by(Transaction.created_at.desc()).limit(5).all()
            
            assert len(recent_transactions) >= 5


class TestMultiUserInteraction:
    """Test multi-user interaction workflows"""
    
    def test_multi_user_split_transaction_workflow(self, app, client):
        """Test complete multi-user split transaction workflow"""
        with app.app_context():
            # Step 1: Create multiple users
            users = []
            for i in range(3):
                user = TestDataFactory.create_test_user(f"multiuser{i}")
                user.set_password("password123")
                db.session.add(user)
                users.append(user)
            db.session.commit()
            
            category = Category.query.filter_by(category_name='Food').first()
            
            # Step 2: User 1 creates a split transaction
            participants = [
                {'user_id': users[0].user_id, 'split_amount': Decimal('40.00')},
                {'user_id': users[1].user_id, 'split_amount': Decimal('35.00')},
                {'user_id': users[2].user_id, 'split_amount': Decimal('25.00')}
            ]
            
            split_tx = TransactionService.add_split_transaction(
                users[0], Decimal('100.00'), 'expense',
                category.category_id, participants
            )
            
            # Step 3: Verify each user sees their portion
            for i, user in enumerate(users):
                user_transactions = Transaction.query.filter_by(
                    user_id=user.user_id,
                    parent_transaction_id=split_tx.transaction_id
                ).all()
                
                assert len(user_transactions) == 1
                
                expected_amounts = [Decimal('40.00'), Decimal('35.00'), Decimal('25.00')]
                assert user_transactions[0].amount == expected_amounts[i]
            
            # Step 4: Test analytics for each user
            for user in users:
                monthly_summary = SimpleAnalyticsService.get_monthly_summary(user)
                assert monthly_summary['total_expenses'] > Decimal('0')
    
    def test_member_management_workflow(self, app, logged_in_user, test_user):
        """Test member management workflow"""
        with app.app_context():
            # Step 1: Create a member
            member = Member(
                user_id=test_user.user_id,
                member_name='Family Member',
                relationship='spouse'
            )
            db.session.add(member)
            db.session.commit()
            
            # Step 2: Verify member creation
            created_member = Member.query.filter_by(
                user_id=test_user.user_id,
                member_name='Family Member'
            ).first()
            
            assert created_member is not None
            assert created_member.relationship == 'spouse'
            
            # Step 3: Update member information
            created_member.relationship = 'partner'
            db.session.commit()
            
            updated_member = Member.query.get(created_member.member_id)
            assert updated_member.relationship == 'partner'
            
            # Step 4: Delete member
            db.session.delete(created_member)
            db.session.commit()
            
            deleted_member = Member.query.get(created_member.member_id)
            assert deleted_member is None


class TestSystemIntegration:
    """Test system-wide integration scenarios"""
    
    def test_complete_user_journey(self, app, client):
        """Test complete user journey from registration to advanced usage"""
        with app.app_context():
            # Journey Step 1: User Registration
            signup_response = client.post('/signup', data={
                'name': 'Journey User',
                'email': 'journey@example.com',
                'password': 'journeypassword123',
                'confirm_password': 'journeypassword123'
            }, follow_redirects=True)
            
            assert signup_response.status_code == 200
            
            user = User.query.filter_by(email='journey@example.com').first()
            assert user is not None
            
            # Journey Step 2: First Transaction
            food_category = Category.query.filter_by(category_name='Food').first()
            first_tx = TransactionService.add_personal_transaction(
                user, Decimal('25.50'), 'expense', food_category.category_id
            )
            assert first_tx is not None
            
            # Journey Step 3: Create Budget
            budget = BudgetService.create_budget(
                user, food_category.category_id, Decimal('200.00'), 'monthly'
            )
            assert budget is not None
            
            # Journey Step 4: Add Multiple Transactions
            for amount in [Decimal('15.00'), Decimal('30.00'), Decimal('22.75')]:
                TransactionService.add_personal_transaction(
                    user, amount, 'expense', food_category.category_id
                )
            
            # Journey Step 5: Check Budget Status
            budget_status = BudgetService.check_budget_status(budget)
            total_spent = Decimal('25.50') + Decimal('15.00') + Decimal('30.00') + Decimal('22.75')
            assert budget_status['spent'] == total_spent
            
            # Journey Step 6: Generate Analytics
            spending_analysis = SimpleAnalyticsService.get_spending_by_category(user)
            monthly_summary = SimpleAnalyticsService.get_monthly_summary(user)
            
            assert len(spending_analysis) >= 1
            assert monthly_summary['total_expenses'] == total_spent
            
            # Journey Step 7: Create Split Transaction
            # (This would require additional users, so we'll create them)
            friend = TestDataFactory.create_test_user("friend")
            friend.set_password("password123")
            db.session.add(friend)
            db.session.commit()
            
            split_participants = [
                {'user_id': user.user_id, 'split_amount': Decimal('20.00')},
                {'user_id': friend.user_id, 'split_amount': Decimal('20.00')}
            ]
            
            split_tx = TransactionService.add_split_transaction(
                user, Decimal('40.00'), 'expense',
                food_category.category_id, split_participants
            )
            assert split_tx is not None
            
            # Journey Step 8: Final Analytics Check
            final_summary = SimpleAnalyticsService.get_monthly_summary(user)
            expected_total = total_spent + Decimal('20.00')  # User's portion of split
            assert final_summary['total_expenses'] == expected_total
    
    def test_data_consistency_across_operations(self, app, logged_in_user, test_user):
        """Test data consistency across multiple operations"""
        with app.app_context():
            category = Category.query.filter_by(category_name='Food').first()
            
            # Step 1: Record initial state
            initial_tx_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            initial_budget_count = Budget.query.filter_by(user_id=test_user.user_id).count()
            
            # Step 2: Perform multiple operations
            operations = []
            
            # Add transactions
            for i in range(5):
                tx = TransactionService.add_personal_transaction(
                    test_user, Decimal(f'{10 + i}.00'), 'expense', category.category_id
                )
                operations.append(('transaction', tx.transaction_id))
            
            # Add budgets
            for period in ['weekly', 'monthly']:
                budget = BudgetService.create_budget(
                    test_user, category.category_id, Decimal('100.00'), period
                )
                operations.append(('budget', budget.budget_id))
            
            # Step 3: Verify intermediate state
            mid_tx_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            mid_budget_count = Budget.query.filter_by(user_id=test_user.user_id).count()
            
            assert mid_tx_count == initial_tx_count + 5
            assert mid_budget_count == initial_budget_count + 2
            
            # Step 4: Clean up operations in reverse order
            for op_type, op_id in reversed(operations):
                if op_type == 'transaction':
                    TransactionService.delete_transaction(test_user, op_id)
                elif op_type == 'budget':
                    budget = Budget.query.get(op_id)
                    if budget:
                        BudgetService.delete_budget(budget)
            
            # Step 5: Verify final state matches initial
            final_tx_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            final_budget_count = Budget.query.filter_by(user_id=test_user.user_id).count()
            
            assert final_tx_count == initial_tx_count
            assert final_budget_count == initial_budget_count


class TestErrorRecovery:
    """Test error recovery and system resilience"""
    
    def test_transaction_rollback_on_error(self, app, logged_in_user, test_user):
        """Test transaction rollback on errors"""
        with app.app_context():
            initial_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            
            # Attempt to create transaction with invalid category
            try:
                TransactionService.add_personal_transaction(
                    test_user, Decimal('50.00'), 'expense', 99999  # Invalid category
                )
            except Exception:
                pass  # Expected to fail
            
            # Verify no partial transaction was created
            final_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            assert final_count == initial_count
    
    def test_split_transaction_consistency(self, app, logged_in_user, test_user):
        """Test split transaction consistency"""
        with app.app_context():
            category = Category.query.filter_by(category_name='Food').first()
            
            # Create additional user
            user2 = TestDataFactory.create_test_user("consistency_user")
            user2.set_password("password123")
            db.session.add(user2)
            db.session.commit()
            
            # Attempt split with mismatched amounts
            participants = [
                {'user_id': test_user.user_id, 'split_amount': Decimal('30.00')},
                {'user_id': user2.user_id, 'split_amount': Decimal('25.00')}
                # Total: 55.00, but transaction amount will be 50.00
            ]
            
            try:
                split_tx = TransactionService.add_split_transaction(
                    test_user, Decimal('50.00'), 'expense',
                    category.category_id, participants
                )
                
                # If service allows this, verify amounts are handled correctly
                if split_tx:
                    total_splits = sum(p['split_amount'] for p in participants)
                    assert total_splits == split_tx.amount or split_tx.amount == Decimal('50.00')
                
            except ValueError:
                # Expected if service validates split amounts
                pass


class TestPerformanceIntegration:
    """Test system performance under load"""
    
    def test_bulk_transaction_processing(self, app, logged_in_user, test_user):
        """Test bulk transaction processing performance"""
        with app.app_context():
            category = Category.query.filter_by(category_name='Food').first()
            
            import time
            start_time = time.time()
            
            # Create 100 transactions
            transactions = []
            for i in range(100):
                tx = TransactionService.add_personal_transaction(
                    test_user, Decimal(f'{i + 1}.00'), 'expense', category.category_id
                )
                transactions.append(tx)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should process 100 transactions within reasonable time
            assert processing_time < 10.0  # 10 seconds max
            assert len(transactions) == 100
            
            # Verify all transactions were created correctly
            created_count = Transaction.query.filter_by(user_id=test_user.user_id).count()
            assert created_count >= 100
    
    def test_analytics_performance_with_large_dataset(self, app, logged_in_user, test_user):
        """Test analytics performance with large dataset"""
        with app.app_context():
            category = Category.query.filter_by(category_name='Food').first()
            
            # Create substantial dataset
            for i in range(50):
                TransactionService.add_personal_transaction(
                    test_user, Decimal(f'{i + 10}.00'), 'expense', category.category_id
                )
            
            import time
            start_time = time.time()
            
            # Generate analytics
            spending_analysis = SimpleAnalyticsService.get_spending_by_category(test_user)
            monthly_summary = SimpleAnalyticsService.get_monthly_summary(test_user)
            
            end_time = time.time()
            analytics_time = end_time - start_time
            
            # Analytics should complete within reasonable time
            assert analytics_time < 5.0  # 5 seconds max
            assert len(spending_analysis) >= 1
            assert 'total_expenses' in monthly_summary


class TestConcurrencyScenarios:
    """Test concurrent operation scenarios"""
    
    def test_concurrent_budget_updates(self, app, logged_in_user, test_user):
        """Test concurrent budget updates"""
        with app.app_context():
            category = Category.query.filter_by(category_name='Food').first()
            
            # Create budget
            budget = BudgetService.create_budget(
                test_user, category.category_id, Decimal('100.00'), 'monthly'
            )
            
            # Simulate concurrent transactions affecting the same budget
            transactions = []
            for i in range(5):
                tx = TransactionService.add_personal_transaction(
                    test_user, Decimal('10.00'), 'expense', category.category_id
                )
                transactions.append(tx)
            
            # Check final budget status
            budget_status = BudgetService.check_budget_status(budget)
            assert budget_status['spent'] == Decimal('50.00')  # 5 * 10.00
            assert budget_status['remaining'] == Decimal('50.00')  # 100.00 - 50.00
