"""Tests for transaction management"""
import pytest
from app.models import Transaction, Category, db
from datetime import datetime


class TestTransactionCreation:
    """Test creating transactions"""

    def test_add_income_transaction(self, app, auth_client, test_user, test_category):
        """Test adding an income transaction"""
        with app.app_context():
            category = Category.query.get(test_category)

        response = auth_client.post('/transactions/add_transaction', data={
            'amount': '1000.00',
            'transaction_type': 'income',
            'category_id': test_category,
            'transaction_date': '2025-11-22'
        }, follow_redirects=True)

        with app.app_context():
            transaction = Transaction.query.filter_by(
                user_id=test_user.user_id,
                transaction_type='income'
            ).first()
            assert transaction is not None
            assert float(transaction.amount) == 1000.00

    def test_add_expense_transaction(self, app, auth_client, test_user, test_category):
        """Test adding an expense transaction"""
        response = auth_client.post('/transactions/add_transaction', data={
            'amount': '50.00',
            'transaction_type': 'expense',
            'category_id': test_category,
            'transaction_date': '2025-11-22'
        }, follow_redirects=True)

        with app.app_context():
            transaction = Transaction.query.filter_by(
                user_id=test_user.user_id,
                transaction_type='expense'
            ).first()
            assert transaction is not None
            assert float(transaction.amount) == 50.00


class TestTransactionEdit:
    """Test editing transactions"""

    @pytest.fixture
    def sample_transaction(self, app, test_user, test_category):
        """Create a sample transaction for editing"""
        with app.app_context():
            category = Category.query.get(test_category)
            transaction = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=100.00,
                transaction_type='expense',
                transaction_date=datetime.now()
            )
            db.session.add(transaction)
            db.session.commit()
            trans_id = transaction.transaction_id

        with app.app_context():
            return Transaction.query.get(trans_id)

    def test_edit_transaction_amount(self, app, auth_client, sample_transaction):
        """Test editing transaction amount"""
        response = auth_client.post(f'/transactions/edit_transaction/{sample_transaction.transaction_id}', data={
            'amount': '150.00',
            'transaction_type': 'expense',
            'category_id': sample_transaction.category_id,
            'transaction_date': sample_transaction.transaction_date.strftime('%Y-%m-%d')
        }, follow_redirects=True)

        with app.app_context():
            updated = Transaction.query.get(sample_transaction.transaction_id)
            assert float(updated.amount) == 150.00


class TestTransactionDelete:
    """Test deleting transactions"""

    @pytest.fixture
    def sample_transaction(self, app, test_user, test_category):
        """Create a sample transaction for deletion"""
        with app.app_context():
            transaction = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=75.00,
                transaction_type='expense',
                transaction_date=datetime.now()
            )
            db.session.add(transaction)
            db.session.commit()
            trans_id = transaction.transaction_id

        with app.app_context():
            return Transaction.query.get(trans_id)

    def test_delete_transaction(self, app, auth_client, sample_transaction):
        """Test deleting a transaction"""
        transaction_id = sample_transaction.transaction_id

        response = auth_client.post(f'/transactions/delete_transaction/{transaction_id}',
                                    follow_redirects=True)

        with app.app_context():
            deleted = Transaction.query.get(transaction_id)
            assert deleted is None


class TestTransactionDisplay:
    """Test transaction display and listing"""

    def test_transactions_page_loads(self, auth_client):
        """Test transactions page is accessible"""
        response = auth_client.get('/transactions/')
        assert response.status_code == 200

    def test_transactions_show_user_data(self, app, auth_client, test_user, test_category):
        """Test user sees their own transactions"""
        # Create transaction for test user
        with app.app_context():
            trans = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=50.00,
                transaction_type='expense',
                transaction_date=datetime.now()
            )
            db.session.add(trans)
            db.session.commit()

        response = auth_client.get('/transactions/')
        assert b'50' in response.data or b'50.00' in response.data
