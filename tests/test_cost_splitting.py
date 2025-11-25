"""Tests for transaction cost splitting logic"""
import pytest
from app.models import Transaction, Member, MembersTransaction, db
from datetime import datetime


class TestPersonalTransactions:
    """Test personal transaction calculations (no members)"""

    @pytest.fixture
    def personal_transaction(self, app, test_user, test_category):
        """Create a personal transaction"""
        with app.app_context():
            trans = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=100.00,
                transaction_type='expense',
                transaction_date=datetime.now(),
                user_participates=True
            )
            db.session.add(trans)
            db.session.commit()
            trans_id = trans.transaction_id

        with app.app_context():
            return Transaction.query.get(trans_id)

    def test_personal_transaction_cost_per_person(self, app, personal_transaction):
        """Test cost per person for personal transaction is full amount"""
        with app.app_context():
            trans = Transaction.query.get(personal_transaction.transaction_id)
            assert trans.is_personal_transaction()
            assert trans.get_cost_per_person() == 100.00

    def test_personal_transaction_user_share(self, app, personal_transaction):
        """Test user pays full amount for personal transaction"""
        with app.app_context():
            trans = Transaction.query.get(personal_transaction.transaction_id)
            assert trans.get_user_share() == 100.00

    def test_personal_transaction_members_share(self, app, personal_transaction):
        """Test members share is 0 for personal transaction"""
        with app.app_context():
            trans = Transaction.query.get(personal_transaction.transaction_id)
            assert trans.get_members_total_share() == 0.00


class TestSharedExpenses:
    """Test shared expense calculations (user + members)"""

    @pytest.fixture
    def shared_transaction(self, app, test_user, test_member, test_category):
        """Create a shared transaction (user + 1 member)"""
        with app.app_context():
            trans = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=100.00,
                transaction_type='expense',
                transaction_date=datetime.now(),
                user_participates=True
            )
            db.session.add(trans)
            db.session.commit()

            # Assign member
            mt = MembersTransaction(
                transaction_id=trans.transaction_id,
                member_id=test_member.member_id
            )
            db.session.add(mt)
            db.session.commit()

            trans_id = trans.transaction_id

        with app.app_context():
            return Transaction.query.get(trans_id)

    def test_shared_expense_cost_per_person(self, app, shared_transaction):
        """Test cost splits evenly: £100 / 2 people = £50 each"""
        with app.app_context():
            trans = Transaction.query.get(shared_transaction.transaction_id)
            assert trans.is_family_expense()
            assert trans.get_cost_per_person() == 50.00  # 100 / 2

    def test_shared_expense_user_share(self, app, shared_transaction):
        """Test user's share is £50"""
        with app.app_context():
            trans = Transaction.query.get(shared_transaction.transaction_id)
            assert trans.get_user_share() == 50.00

    def test_shared_expense_members_share(self, app, shared_transaction):
        """Test members' total share is £50"""
        with app.app_context():
            trans = Transaction.query.get(shared_transaction.transaction_id)
            assert trans.get_members_total_share() == 50.00


class TestMembersOnlyExpenses:
    """Test members-only expenses (user pays but doesn't participate)"""

    @pytest.fixture
    def members_only_transaction(self, app, test_user, test_member, test_category):
        """Create transaction where user pays but doesn't participate"""
        with app.app_context():
            trans = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=100.00,
                transaction_type='expense',
                transaction_date=datetime.now(),
                user_participates=False
            )
            db.session.add(trans)
            db.session.commit()

            # Assign member
            mt = MembersTransaction(
                transaction_id=trans.transaction_id,
                member_id=test_member.member_id
            )
            db.session.add(mt)
            db.session.commit()

            trans_id = trans.transaction_id

        with app.app_context():
            return Transaction.query.get(trans_id)

    def test_members_only_cost_per_person(self, app, members_only_transaction):
        """Test cost per person is full amount (only 1 member)"""
        with app.app_context():
            trans = Transaction.query.get(
                members_only_transaction.transaction_id)
            assert trans.is_members_only_expense()
            assert trans.get_cost_per_person() == 100.00  # 100 / 1 member

    def test_members_only_user_share(self, app, members_only_transaction):
        """Test user's share is 0 (doesn't participate)"""
        with app.app_context():
            trans = Transaction.query.get(
                members_only_transaction.transaction_id)
            assert trans.get_user_share() == 0.00

    def test_members_only_members_share(self, app, members_only_transaction):
        """Test members' share is full £100"""
        with app.app_context():
            trans = Transaction.query.get(
                members_only_transaction.transaction_id)
            assert trans.get_members_total_share() == 100.00


class TestIncomeTransactions:
    """Test income transaction handling"""

    @pytest.fixture
    def income_transaction(self, app, test_user, test_category):
        """Create an income transaction"""
        with app.app_context():
            trans = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=1000.00,
                transaction_type='income',
                transaction_date=datetime.now()
            )
            db.session.add(trans)
            db.session.commit()
            trans_id = trans.transaction_id

        with app.app_context():
            return Transaction.query.get(trans_id)

    def test_income_not_split(self, app, income_transaction):
        """Test income is not split among members"""
        with app.app_context():
            trans = Transaction.query.get(income_transaction.transaction_id)
            assert trans.transaction_type == 'income'
            # Income transactions don't use splitting logic
            assert trans.amount == 1000.00
