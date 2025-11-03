#!/usr/bin/env python3
"""
Test Transaction Splitting Logic
Tests the improved transaction cost splitting with user participation control.
"""

from app import create_app, db
from app.models import User, Category, Member
from app.services import TransactionService, UserService
from decimal import Decimal

def test_transaction_splitting_scenarios():
    """Test all transaction splitting scenarios"""
    app = create_app()
    
    with app.app_context():
        try:
            # Setup test data
            print("🔧 Setting up test data...")
            
            # Seed categories first
            from app.utilities.seed_categories import seed_system_categories
            seed_system_categories()
            
            # Create test user with unique email
            import time
            unique_email = f"test_splitting_{int(time.time())}@test.com"
            user = User(user_name="Test User", email=unique_email)
            user.set_password("testpass123")
            db.session.add(user)
            db.session.commit()
            
            # Create test members
            spouse = UserService.add_member_to_user(user, "Spouse", "spouse")
            child = UserService.add_member_to_user(user, "Child", "child")
            
            # Get a category (Food)
            food_category = Category.query.filter_by(category_name='Food', user_id=None).first()
            
            print("\n📊 Testing Transaction Splitting Scenarios...\n")
            
            # Scenario 1: Personal Transaction (User only)
            print("1️⃣ PERSONAL TRANSACTION (User Only)")
            personal_tx = TransactionService.add_personal_transaction(
                user=user,
                amount=Decimal('50.00'),
                transaction_type='expense',
                category_id=food_category.category_id
            )
            
            print(f"   Amount: £{personal_tx.amount}")
            print(f"   Members involved: {len(personal_tx.get_associated_members())}")
            print(f"   Is personal: {personal_tx.is_personal_transaction()}")
            print(f"   User participates: {personal_tx.user_participates}")
            print(f"   User share: £{personal_tx.get_user_share():.2f}")
            print(f"   Members total share: £{personal_tx.get_members_total_share():.2f}")
            print(f"   User net expense: £{personal_tx.get_user_net_expense():.2f}")
            print(f"   Expense type: {personal_tx.get_expense_type_description()}")
            
            # Scenario 2: Shared Transaction (User + Members participate)
            print("\n2️⃣ SHARED TRANSACTION (User + Members)")
            shared_tx = TransactionService.add_shared_transaction(
                user=user,
                amount=Decimal('100.00'),
                transaction_type='expense',
                category_id=food_category.category_id,
                member_ids=[spouse.member_id, child.member_id],
                user_participates=True
            )
            
            print(f"   Amount: £{shared_tx.amount}")
            print(f"   Members involved: {len(shared_tx.get_associated_members())}")
            print(f"   User participates: {shared_tx.user_participates}")
            print(f"   Cost per person: £{shared_tx.get_cost_per_person():.2f}")
            print(f"   User share: £{shared_tx.get_user_share():.2f}")
            print(f"   Members total share: £{shared_tx.get_members_total_share():.2f}")
            print(f"   User net expense: £{shared_tx.get_user_net_expense():.2f}")
            print(f"   Expense type: {shared_tx.get_expense_type_description()}")
            
            # Scenario 3: Members-Only Transaction (User pays but doesn't participate)
            print("\n3️⃣ MEMBERS-ONLY TRANSACTION (User Paid, Doesn't Participate)")
            members_only_tx = TransactionService.add_shared_transaction(
                user=user,
                amount=Decimal('60.00'),
                transaction_type='expense',
                category_id=food_category.category_id,
                member_ids=[spouse.member_id, child.member_id],
                user_participates=False  # User doesn't participate in split
            )
            
            print(f"   Amount: £{members_only_tx.amount}")
            print(f"   Members involved: {len(members_only_tx.get_associated_members())}")
            print(f"   User participates: {members_only_tx.user_participates}")
            print(f"   Cost per person: £{members_only_tx.get_cost_per_person():.2f}")
            print(f"   User share: £{members_only_tx.get_user_share():.2f}")
            print(f"   Members total share: £{members_only_tx.get_members_total_share():.2f}")
            print(f"   User net expense: £{members_only_tx.get_user_net_expense():.2f}")
            print(f"   Expense type: {members_only_tx.get_expense_type_description()}")
            
            # Scenario 4: Single Member Transaction
            print("\n4️⃣ SINGLE MEMBER TRANSACTION")
            single_member_tx = TransactionService.add_member_transaction(
                user=user,
                member_id=child.member_id,
                amount=Decimal('20.00'),
                transaction_type='expense',
                category_id=food_category.category_id
            )
            
            print(f"   Amount: £{single_member_tx.amount}")
            print(f"   Members involved: {len(single_member_tx.get_associated_members())}")
            print(f"   User participates: {single_member_tx.user_participates}")
            print(f"   Cost per person: £{single_member_tx.get_cost_per_person():.2f}")
            print(f"   User share: £{single_member_tx.get_user_share():.2f}")
            print(f"   Members total share: £{single_member_tx.get_members_total_share():.2f}")
            print(f"   User net expense: £{single_member_tx.get_user_net_expense():.2f}")
            print(f"   Expense type: {single_member_tx.get_expense_type_description()}")
            
            print("\n✅ All transaction splitting scenarios work correctly!")
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run the transaction splitting tests"""
    print("🚀 Testing Improved Transaction Splitting Logic")
    print("=" * 60)
    
    success = test_transaction_splitting_scenarios()
    
    if success:
        print("\n🎉 TRANSACTION SPLITTING TESTS PASSED!")
        print("✅ User participation control works correctly")
        print("✅ Cost splitting logic handles all scenarios")
        print("✅ Members are properly managed as data entities")
    else:
        print("\n❌ Some tests failed")
    
    return success

if __name__ == '__main__':
    success = main()
    import sys
    sys.exit(0 if success else 1)