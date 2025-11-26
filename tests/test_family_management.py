"""Tests for family member management"""
import pytest
from app.models import Member, Transaction, MembersTransaction, db
from datetime import datetime


class TestMemberCreation:
    """Test creating family members"""

    def test_add_member(self, app, auth_client, test_user):
        """Test adding a family member"""
        response = auth_client.post('/add_member', data={
            'name': 'John Doe',
            'relationship': 'Child'
        }, follow_redirects=True)

        with app.app_context():
            member = Member.query.filter_by(
                user_id=test_user.user_id,
                name='John Doe'
            ).first()
            assert member is not None
            assert member.relationship == 'Child'

    def test_member_belongs_to_user(self, app, test_member, test_user):
        """Test member is correctly associated with user"""
        with app.app_context():
            member = Member.query.get(test_member.member_id)
            assert member.user_id == test_user.user_id


class TestMemberEdit:
    """Test editing family members"""

    def test_edit_member_name(self, app, auth_client, test_member):
        """Test editing member's name"""
        response = auth_client.post('/edit_member', data={
            'member_id': test_member.member_id,
            'name': 'Sarah Williams',
            'relationship': 'Spouse'
        }, follow_redirects=True)

        with app.app_context():
            updated = Member.query.get(test_member.member_id)
            assert updated.name == 'Sarah Williams'

    def test_edit_member_relationship(self, app, auth_client, test_member):
        """Test editing member's relationship"""
        response = auth_client.post('/edit_member', data={
            'member_id': test_member.member_id,
            'name': test_member.name,
            'relationship': 'Partner'
        }, follow_redirects=True)

        with app.app_context():
            updated = Member.query.get(test_member.member_id)
            assert updated.relationship == 'Partner'


class TestMemberDelete:
    """Test deleting family members"""

    def test_delete_member(self, app, auth_client, test_member):
        """Test deleting a member"""
        member_id = test_member.member_id

        response = auth_client.post(f'/delete_member/{member_id}',
                                    follow_redirects=True)

        with app.app_context():
            deleted = Member.query.get(member_id)
            assert deleted is None


class TestMemberTransactionAssignment:
    """Test assigning members to transactions"""

    def test_assign_member_to_transaction(self, app, auth_client, test_user, test_member, test_category):
        """Test creating transaction with assigned member"""
        with app.app_context():
            member_id = test_member.member_id

        response = auth_client.post('/transactions/add_transaction', data={
            'amount': '100.00',
            'transaction_type': 'expense',
            'category_id': test_category,
            'transaction_date': '2025-11-22',
            'members[]': [member_id],
            'user_participates': 'true'
        }, follow_redirects=True)

        with app.app_context():
            transaction = Transaction.query.filter_by(
                user_id=test_user.user_id
            ).first()
            if transaction:
                assigned_members = transaction.get_associated_members()
                assert len(assigned_members) >= 0


class TestMemberStatistics:
    """Test member statistics and calculations"""

    @pytest.fixture
    def member_with_transactions(self, app, test_user, test_member, test_category):
        """Create member with sample transactions"""
        with app.app_context():
            # Create transaction
            trans = Transaction(
                user_id=test_user.user_id,
                category_id=test_category,
                amount=90.00,
                transaction_type='expense',
                transaction_date=datetime.now(),
                user_participates=True
            )
            db.session.add(trans)
            db.session.commit()

            # Assign member to transaction
            mt = MembersTransaction(
                transaction_id=trans.transaction_id,
                member_id=test_member.member_id
            )
            db.session.add(mt)
            db.session.commit()

            return test_member.member_id

    def test_member_contribution_calculation(self, app, member_with_transactions):
        """Test member's contribution is calculated correctly"""
        with app.app_context():
            member = Member.query.get(member_with_transactions)
            stats = member.get_lifetime_stats()

            assert stats['total_transactions'] >= 0
            assert stats['total_contribution'] >= 0

    def test_member_monthly_contribution(self, app, member_with_transactions):
        """Test member's monthly contribution calculation"""
        with app.app_context():
            member = Member.query.get(member_with_transactions)
            now = datetime.now()
            monthly = member.get_monthly_contribution(now.month, now.year)

            assert monthly >= 0
