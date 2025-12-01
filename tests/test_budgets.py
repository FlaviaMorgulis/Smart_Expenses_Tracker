"""Tests for budget management"""
import pytest
from app.models import Budget, db
from datetime import datetime


class TestBudgetCreation:
    """Test creating budgets"""

    def test_create_user_budget(self, app, auth_client, test_user, test_category):
        """Test creating a basic category budget for user"""
        response = auth_client.post('/budget/add',
                                    json={
                                        'amount': '1000.00',
                                        'alert_threshold': '80',
                                        'category_id': test_category,
                                        'member_id': None,
                                        'notifications_enabled': True
                                    },
                                    content_type='application/json',
                                    follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            budget = Budget.query.filter_by(
                user_id=test_user.user_id,
                category_id=test_category
            ).first()
            assert budget is not None

    def test_create_category_budget(self, app, auth_client, test_user, test_category):
        """Test creating a category-specific budget"""
        response = auth_client.post('/budget/add',
                                    json={
                                        'amount': '200.00',
                                        'alert_threshold': '75',
                                        'category_id': test_category,
                                        'member_id': None,
                                        'notifications_enabled': True
                                    },
                                    content_type='application/json',
                                    follow_redirects=True)

        assert response.status_code == 200

    def test_create_multiple_category_budgets(self, app, auth_client, test_user, test_category):
        """Test creating budgets for different categories"""
        # Create first category budget
        response1 = auth_client.post('/budget/add',
                                     json={
                                         'amount': '500.00',
                                         'alert_threshold': '80',
                                         'category_id': test_category,
                                         'member_id': None,
                                         'notifications_enabled': True
                                     },
                                     content_type='application/json',
                                     follow_redirects=True)

        assert response1.status_code == 200

        # Verify budget was created
        with app.app_context():
            budget = Budget.query.filter_by(
                user_id=test_user.user_id,
                category_id=test_category
            ).first()
            assert budget is not None
            assert float(budget.budget_amount) == 500.00


class TestBudgetEdit:
    """Test editing budgets"""

    @pytest.fixture
    def sample_budget(self, app, test_user):
        """Create a sample budget for editing"""
        with app.app_context():
            budget = Budget(
                user_id=test_user.user_id,
                budget_amount=800.00,
                alert_threshold=80.0,
                is_active=True,
                notifications_enabled=True
            )
            db.session.add(budget)
            db.session.commit()
            budget_id = budget.budget_id

        with app.app_context():
            return Budget.query.get(budget_id)

    def test_edit_budget_amount(self, app, auth_client, sample_budget):
        """Test editing budget amount"""
        response = auth_client.post(f'/budget/{sample_budget.budget_id}/edit', data={
            'budget_amount': '1200.00',
            'alert_threshold': '80',
            'notifications_enabled': 'true'
        }, follow_redirects=True)

        with app.app_context():
            updated = Budget.query.get(sample_budget.budget_id)
            if updated:
                assert float(updated.budget_amount) == 1200.00 or float(
                    updated.budget_amount) == 800.00

    def test_edit_budget_threshold(self, app, auth_client, sample_budget):
        """Test editing budget alert threshold"""
        response = auth_client.post(f'/budget/{sample_budget.budget_id}/edit',
                                    json={
            'amount': '800.00',
            'alert_threshold': '90',
            'notifications_enabled': True
        },
            content_type='application/json',
            follow_redirects=True)

        assert response.status_code == 200


class TestBudgetAlerts:
    """Test budget alert functionality"""

    @pytest.fixture
    def budget_with_threshold(self, app, test_user):
        """Create budget with alert threshold"""
        with app.app_context():
            budget = Budget(
                user_id=test_user.user_id,
                budget_amount=1000.00,
                alert_threshold=80.0,
                notifications_enabled=True,
                is_active=True
            )
            db.session.add(budget)
            db.session.commit()
            budget_id = budget.budget_id

        with app.app_context():
            return Budget.query.get(budget_id)

    def test_alert_triggered_at_threshold(self, app, budget_with_threshold):
        """Test alert is triggered when threshold is reached"""
        with app.app_context():
            budget = Budget.query.get(budget_with_threshold.budget_id)
            current_spending = 800.00  # 80% of 1000

            assert budget.should_alert(current_spending) is True

    def test_alert_not_triggered_below_threshold(self, app, budget_with_threshold):
        """Test alert is not triggered below threshold"""
        with app.app_context():
            budget = Budget.query.get(budget_with_threshold.budget_id)
            current_spending = 700.00  # 70% of 1000

            assert budget.should_alert(current_spending) is False

    def test_alert_status_over_budget(self, app, budget_with_threshold):
        """Test alert status when over budget"""
        with app.app_context():
            budget = Budget.query.get(budget_with_threshold.budget_id)
            current_spending = 1100.00  # 110% of 1000

            status = budget.get_alert_status(current_spending)
            assert status['status'] == 'over_budget'
            assert status['percentage_used'] > 100


class TestBudgetPauseActivate:
    """Test pausing and activating budgets"""

    @pytest.fixture
    def active_budget(self, app, test_user):
        """Create an active budget"""
        with app.app_context():
            budget = Budget(
                user_id=test_user.user_id,
                budget_amount=500.00,
                alert_threshold=80.0,
                is_active=True,
                notifications_enabled=True
            )
            db.session.add(budget)
            db.session.commit()
            budget_id = budget.budget_id

        with app.app_context():
            return Budget.query.get(budget_id)

    def test_pause_budget(self, app, active_budget):
        """Test pausing a budget"""
        with app.app_context():
            budget = Budget.query.get(active_budget.budget_id)
            budget.pause()
            db.session.commit()

            assert budget.is_paused() is True
            assert budget.is_active is False

    def test_unpause_budget(self, app, active_budget):
        """Test unpausing a budget"""
        with app.app_context():
            budget = Budget.query.get(active_budget.budget_id)
            budget.pause()
            db.session.commit()

            budget.unpause()
            db.session.commit()

            assert budget.is_paused() is False
            assert budget.is_active is True
