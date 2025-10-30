"""
Test Transaction Model Relationships
Tests the relationships between Transaction, Category, User, and Members models.
"""

from app import create_app, db
from app.models import User, Category, Member, Transaction, MembersTransaction
from datetime import datetime, date
from decimal import Decimal
import sys

def test_transaction_category_relationships():
    """Test Transaction-Category relationships"""
    print("🧪 Testing Transaction-Category Relationships...")
    
    # Create test user
    test_user = User(user_name="Test User", email="test@example.com")
    test_user.set_password("testpass123")
    db.session.add(test_user)
    db.session.commit()
    
    # Get a system category
    food_category = Category.query.filter_by(category_name='Food', user_id=None).first()
    if not food_category:
        print("❌ Food category not found. Run seed_categories.py first!")
        return False
    
    # Test 1: Create transaction with category
    print("  Test 1: Creating transaction with category...")
    transaction1 = Transaction(
        user_id=test_user.user_id,
        category_id=food_category.category_id,
        amount=Decimal('25.50'),
        transaction_type='expense',
        transaction_date=datetime.now()
    )
    db.session.add(transaction1)
    db.session.commit()
    
    # Verify relationship works
    assert transaction1.category.category_name == 'Food'
    assert food_category.transactions[0] == transaction1
    print("  ✅ Transaction-Category relationship working")
    
    # Test 2: Create transaction without category
    print("  Test 2: Creating transaction without category...")
    transaction2 = Transaction(
        user_id=test_user.user_id,
        category_id=None,  # No category
        amount=Decimal('10.00'),
        transaction_type='expense',
        transaction_date=datetime.now()
    )
    db.session.add(transaction2)
    db.session.commit()
    
    assert transaction2.category is None
    print("  ✅ Transaction without category working")
    
    # Test 3: Category deletion (SET NULL behavior)
    print("  Test 3: Testing category deletion (SET NULL)...")
    
    # Create a test user category (custom category)
    test_category = Category(category_name='MyCustomCategory', user_id=test_user.user_id)
    db.session.add(test_category)
    db.session.commit()
    
    # Create transaction with test category
    transaction3 = Transaction(
        user_id=test_user.user_id,
        category_id=test_category.category_id,
        amount=Decimal('5.00'),
        transaction_type='expense',
        transaction_date=datetime.now()
    )
    db.session.add(transaction3)
    db.session.commit()
    
    # Delete the category
    db.session.delete(test_category)
    db.session.commit()
    
    # Refresh transaction and check category is NULL
    db.session.refresh(transaction3)
    assert transaction3.category_id is None
    assert transaction3.category is None
    print("  ✅ Category deletion SET NULL working")
    
    return True

def test_transaction_member_relationships():
    """Test Transaction-Member many-to-many relationships"""
    print("🧪 Testing Transaction-Member Relationships...")
    
    # Get test user
    test_user = User.query.filter_by(email="test@example.com").first()
    
    # Create test members
    member1 = Member(user_id=test_user.user_id, name="Alice", relationship="spouse")
    member2 = Member(user_id=test_user.user_id, name="Bob", relationship="child")
    db.session.add_all([member1, member2])
    db.session.commit()
    
    # Create transaction
    transaction = Transaction(
        user_id=test_user.user_id,
        amount=Decimal('100.00'),
        transaction_type='expense',
        transaction_date=datetime.now()
    )
    db.session.add(transaction)
    db.session.commit()
    
    # Test 1: Associate members with transaction
    print("  Test 1: Associating members with transaction...")
    
    member_transaction1 = MembersTransaction(transaction_id=transaction.transaction_id, member_id=member1.member_id)
    member_transaction2 = MembersTransaction(transaction_id=transaction.transaction_id, member_id=member2.member_id)
    
    db.session.add_all([member_transaction1, member_transaction2])
    db.session.commit()
    
    # Verify relationships
    associated_members = transaction.get_associated_members()
    assert len(associated_members) == 2
    assert member1 in associated_members
    assert member2 in associated_members
    print("  ✅ Member-Transaction associations working")
    
    # Test 2: Personal transaction check
    print("  Test 2: Testing personal transaction detection...")
    
    personal_transaction = Transaction(
        user_id=test_user.user_id,
        amount=Decimal('20.00'),
        transaction_type='expense',
        transaction_date=datetime.now()
    )
    db.session.add(personal_transaction)
    db.session.commit()
    
    assert personal_transaction.is_personal_transaction() == True
    assert transaction.is_personal_transaction() == False
    print("  ✅ Personal transaction detection working")
    
    # Test 3: Cascade delete behavior
    print("  Test 3: Testing cascade delete behavior...")
    
    # Delete transaction - should cascade delete member associations
    initial_member_transactions = MembersTransaction.query.count()
    db.session.delete(transaction)
    db.session.commit()
    
    final_member_transactions = MembersTransaction.query.count()
    assert final_member_transactions == initial_member_transactions - 2
    print("  ✅ Cascade delete working")
    
    return True

def test_transaction_serialization():
    """Test Transaction to_dict() method"""
    print("🧪 Testing Transaction Serialization...")
    
    test_user = User.query.filter_by(email="test@example.com").first()
    food_category = Category.query.filter_by(category_name='Food', user_id=None).first()
    
    transaction = Transaction(
        user_id=test_user.user_id,
        category_id=food_category.category_id,
        amount=Decimal('15.75'),
        transaction_type='expense',
        transaction_date=datetime(2025, 10, 27, 14, 30)
    )
    db.session.add(transaction)
    db.session.commit()
    
    # Test serialization
    data = transaction.to_dict()
    
    assert data['amount'] == 15.75
    assert data['type'] == 'expense'
    assert data['category'] == 'Food'
    assert data['is_personal'] == True
    assert 'transaction_id' in data
    assert 'date' in data
    
    print("  ✅ Transaction serialization working")
    return True

def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    # Delete test user and cascading data
    test_user = User.query.filter_by(email="test@example.com").first()
    if test_user:
        db.session.delete(test_user)
        db.session.commit()
    
    print("  ✅ Test data cleaned up")

def main():
    """Run all tests"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Starting Transaction Model Relationship Tests...")
            
            # Run tests
            if not test_transaction_category_relationships():
                print("❌ Transaction-Category tests failed!")
                return
                
            if not test_transaction_member_relationships():
                print("❌ Transaction-Member tests failed!")
                return
                
            if not test_transaction_serialization():
                print("❌ Transaction serialization tests failed!")
                return
            
            print("\n🎉 All Transaction relationship tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cleanup_test_data()

if __name__ == '__main__':
    main()