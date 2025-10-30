"""
Full Integration Test Suite
Tests the complete backend system including models, services, auth integration, and all relationships.
"""

from app import create_app, db
from app.models import User, Category, Member, Transaction, MembersTransaction, Budget
from app.services import (
    UserService, TransactionService, AnalyticsService, 
    ExportService, MemberService, CategoryService, BudgetService
)
from app.utils import ValidationHelper, format_currency, calculate_percentage
from datetime import datetime, date
from decimal import Decimal
import sys

def setup_test_environment():
    """Set up test environment with sample data"""
    print("🔧 Setting up test environment...")
    
    # Create tables
    db.create_all()
    
    # Initialize system categories using seed script
    from seed_categories import seed_system_categories
    seed_system_categories()
    
    # Create test user
    test_user = User(user_name="John Doe", email="test@integration.com")
    test_user.set_password("testpass123")
    db.session.add(test_user)
    db.session.commit()
    
    print(f"✅ Test user created: {test_user.user_name} (ID: {test_user.user_id})")
    return test_user

def test_auth_integration(test_user):
    """Test authentication integration with User model"""
    print("\n🔐 Testing Auth Integration...")
    
    # Test 1: Password authentication
    assert test_user.check_password("testpass123") == True
    assert test_user.check_password("wrongpass") == False
    print("  ✅ Password authentication working")
    
    # Test 2: Flask-Login integration
    assert test_user.get_id() == str(test_user.user_id)
    assert test_user.is_authenticated == True
    print("  ✅ Flask-Login integration working")
    
    # Test 3: User serialization
    user_dict = test_user.to_dict()
    assert 'user_id' in user_dict
    assert user_dict['email'] == "test@integration.com"
    assert 'password_hash' not in user_dict  # Should not expose password
    print("  ✅ User serialization working")
    
    return True

def test_category_system():
    """Test category system and service integration"""
    print("\n📂 Testing Category System...")
    
    # Test 1: System categories exist (using model directly)
    from app.models import Category
    categories = Category.query.all()
    assert len(categories) >= 7  # Default categories
    print(f"  ✅ Found {len(categories)} categories")
    
    # Test 2: Get category by name (using model directly)
    food_category = Category.query.filter_by(category_name='Food', user_id=None).first()
    assert food_category is not None
    assert food_category.user_id is None  # System category
    print("  ✅ Category lookup working")
    
    # Test 3: Category relationships
    assert hasattr(food_category, 'transactions')
    print("  ✅ Category relationships working")
    
    return True

def test_member_management(test_user):
    """Test member management and relationships"""
    print("\n👥 Testing Member Management...")
    
    # Test 1: Add members using service
    spouse = UserService.add_member_to_user(
        user=test_user, 
        name="Jane Doe", 
        relationship="spouse"
    )
    child = UserService.add_member_to_user(
        user=test_user,
        name="Tommy Doe", 
        relationship="child"
    )
    
    assert spouse.user_id == test_user.user_id
    assert child.user_id == test_user.user_id
    print(f"  ✅ Added members: {spouse.name}, {child.name}")
    
    # Test 2: Member relationships
    assert len(test_user.members) == 2
    assert spouse in test_user.members
    print("  ✅ Member relationships working")
    
    # Test 3: Member serialization
    member_dict = spouse.to_dict()
    assert member_dict['name'] == "Jane Doe"
    assert member_dict['relationship'] == "spouse"
    print("  ✅ Member serialization working")
    
    return spouse, child

def test_transaction_services(test_user, spouse, child):
    """Test transaction services and relationships"""
    print("\n💰 Testing Transaction Services...")
    
    from app.models import Category
    food_category = Category.query.filter_by(category_name='Food', user_id=None).first()
    transport_category = Category.query.filter_by(category_name='Transport', user_id=None).first()
    
    # Test 1: Personal transactions
    personal_tx = TransactionService.add_personal_transaction(
        user=test_user,
        amount=Decimal('50.00'),
        transaction_type='expense',
        category_id=food_category.category_id
    )
    
    assert personal_tx.user_id == test_user.user_id
    assert personal_tx.is_personal_transaction() == True
    assert len(personal_tx.get_associated_members()) == 0
    print("  ✅ Personal transaction created")
    
    # Test 2: Member transactions
    member_tx = TransactionService.add_member_transaction(
        user=test_user,
        member_id=spouse.member_id,
        amount=Decimal('75.00'),
        transaction_type='expense',
        category_id=transport_category.category_id
    )
    
    assert member_tx.user_id == test_user.user_id
    assert member_tx.is_personal_transaction() == False
    assert len(member_tx.get_associated_members()) == 1
    assert spouse in member_tx.get_associated_members()
    print("  ✅ Member transaction created")
    
    # Test 3: Transaction serialization
    tx_dict = personal_tx.to_dict()
    assert tx_dict['amount'] == 50.00
    assert tx_dict['category'] == 'Food'
    assert tx_dict['is_personal'] == True
    print("  ✅ Transaction serialization working")
    
    # Test 4: Multiple members on one transaction
    TransactionService.add_member_to_transaction(member_tx, child.member_id)
    assert len(member_tx.get_associated_members()) == 2
    print("  ✅ Multiple members per transaction working")
    
    return personal_tx, member_tx

def test_analytics_services(test_user):
    """Test analytics and reporting services"""
    print("\n📊 Testing Analytics Services...")
    
    # Test 1: Spending by category
    spending_breakdown = AnalyticsService.get_spending_by_category(
        user=test_user,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31)
    )
    
    assert len(spending_breakdown) > 0
    print(f"  ✅ Spending breakdown: {len(spending_breakdown)} categories")
    
    # Test 2: Monthly summary
    monthly_summary = AnalyticsService.get_monthly_summary(
        user=test_user,
        year=2025,
        month=10
    )
    
    assert 'income' in monthly_summary
    assert 'expenses' in monthly_summary
    assert 'balance' in monthly_summary
    print("  ✅ Monthly summary working")
    
    return True

def test_budget_system(test_user, spouse):
    """Test budget system and tracking"""
    print("\n💳 Testing Budget System...")
    
    from app.models import Category
    food_category = Category.query.filter_by(category_name='Food', user_id=None).first()
    
    # Test 1: Create user budget
    user_budget = BudgetService.create_user_budget(
        user_id=test_user.user_id,
        category_id=food_category.category_id,
        budget_amount=Decimal('200.00'),
        budget_period='monthly'
    )
    
    assert user_budget.user_id == test_user.user_id
    assert user_budget.is_user_budget() == True
    assert user_budget.is_category_budget() == True
    print("  ✅ User category budget created")
    
    # Test 2: Create member budget
    member_budget = BudgetService.create_member_budget(
        member_id=spouse.member_id,
        category_id=None,  # Total expenses
        budget_amount=Decimal('300.00'),
        budget_period='monthly'
    )
    
    assert member_budget.member_id == spouse.member_id
    assert member_budget.is_member_budget() == True
    assert member_budget.is_total_budget() == True
    print("  ✅ Member total budget created")
    
    # Test 3: Budget usage tracking
    budget_usage = BudgetService.get_budget_usage(user_budget.budget_id)
    assert 'budget_amount' in budget_usage
    assert 'amount_spent' in budget_usage
    assert 'percentage_used' in budget_usage
    print("  ✅ Budget usage tracking working")
    
    return True

def test_data_export(test_user):
    """Test data export functionality"""
    print("\n📤 Testing Data Export...")
    
    # Test export service
    export_data = ExportService.export_user_data(
        user=test_user,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31)
    )
    
    assert 'user_info' in export_data
    assert 'members' in export_data
    assert 'personal_transactions' in export_data
    assert 'member_transactions' in export_data
    
    # Check user info
    assert export_data['user_info']['name'] == test_user.user_name
    assert export_data['user_info']['email'] == test_user.email
    
    print("  ✅ Data export working")
    return True

def test_validation_utilities():
    """Test validation utilities"""
    print("\n✅ Testing Validation Utilities...")
    
    # Test 1: Email validation
    assert ValidationHelper.validate_user_data("John", "john@test.com", "password123") == []
    errors = ValidationHelper.validate_user_data("", "invalid-email", "123")
    assert len(errors) > 0
    print("  ✅ User data validation working")
    
    # Test 2: Transaction validation
    from app.utils import validate_transaction_amount, validate_email
    assert validate_transaction_amount(50.00) == True
    assert validate_transaction_amount(-10) == False
    assert validate_email("test@example.com") == True
    assert validate_email("invalid") == False
    print("  ✅ Utility functions working")
    
    # Test 3: Currency formatting
    assert format_currency(123.45) == "$123.45"
    assert calculate_percentage(25, 100) == 25.0
    print("  ✅ Formatting utilities working")
    
    return True

def test_cascade_behavior(test_user):
    """Test cascade delete behavior"""
    print("\n🗑️  Testing Cascade Behavior...")
    
    # Count initial records
    initial_transactions = Transaction.query.filter_by(user_id=test_user.user_id).count()
    initial_members = Member.query.filter_by(user_id=test_user.user_id).count()
    initial_budgets = Budget.query.filter_by(user_id=test_user.user_id).count()
    
    print(f"  Initial counts - Transactions: {initial_transactions}, Members: {initial_members}, Budgets: {initial_budgets}")
    
    # This would delete user and cascade all related data
    # (We won't actually delete in the test, just verify the relationships exist)
    assert len(test_user.transactions) > 0
    assert len(test_user.members) > 0
    assert len(test_user.budgets) > 0
    
    print("  ✅ Cascade relationships verified")
    return True

def cleanup_test_data():
    """Clean up all test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test user (should cascade delete everything)
    test_user = User.query.filter_by(email="test@integration.com").first()
    if test_user:
        db.session.delete(test_user)
        db.session.commit()
    
    print("  ✅ Test data cleaned up")

def main():
    """Run complete integration test suite"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Starting Full Integration Test Suite...")
            print("=" * 60)
            
            # Setup
            test_user = setup_test_environment()
            
            # Run all tests
            test_auth_integration(test_user)
            test_category_system()
            spouse, child = test_member_management(test_user)
            personal_tx, member_tx = test_transaction_services(test_user, spouse, child)
            test_analytics_services(test_user)
            test_budget_system(test_user, spouse)
            test_data_export(test_user)
            test_validation_utilities()
            test_cascade_behavior(test_user)
            
            print("\n" + "=" * 60)
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Your backend system is fully functional and integrated!")
            print("✅ Models, Services, Auth, and Utilities all working together!")
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cleanup_test_data()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)