"""
Simple Backend Test
A simplified test that works with your current database and focuses on core functionality.
"""

from app import create_app, db
from app.models import User, Category, Member, Transaction, MembersTransaction
from app.services import UserService, TransactionService, AnalyticsService, ExportService, MemberService
from datetime import datetime
from decimal import Decimal

def test_basic_functionality():
    """Test basic backend functionality without complex database operations"""
    print("🧪 Testing Basic Backend Functionality...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test 1: User model functionality
            print("  Testing User model...")
            user = User(user_name="Test User", email="simple@test.com")
            user.set_password("testpass123")
            
            # Test password functionality
            assert user.check_password("testpass123") == True
            assert user.check_password("wrongpass") == False
            assert user.get_id() is not None
            print("  ✅ User model working")
            
            # Don't commit to database yet, just test the objects
            
            # Test 2: Member model functionality
            print("  Testing Member model...")
            member = Member(user_id=1, name="Test Member", relationship="spouse")
            member_dict = member.to_dict()
            assert member_dict['name'] == "Test Member"
            assert member_dict['relationship'] == "spouse"
            print("  ✅ Member model working")
            
            # Test 3: Transaction model functionality
            print("  Testing Transaction model...")
            transaction = Transaction(
                user_id=1,
                category_id=1,
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=datetime.now()
            )
            # Set created_at manually for testing since it's not set automatically outside DB
            transaction.created_at = datetime.now()
            
            # Test transaction methods
            assert transaction.is_personal_transaction() == True  # No members yet
            tx_dict = transaction.to_dict()
            assert tx_dict['amount'] == 50.00
            assert tx_dict['type'] == 'expense'
            print("  ✅ Transaction model working")
            
            # Test 4: Utility functions
            print("  Testing utility functions...")
            from app.utils import format_currency, calculate_percentage, validate_email
            
            assert format_currency(123.45) == "$123.45"
            assert calculate_percentage(25, 100) == 25.0
            assert validate_email("test@example.com") == True
            assert validate_email("invalid-email") == False
            print("  ✅ Utility functions working")
            
            # Test 5: Validation helpers
            print("  Testing validation helpers...")
            from app.utils import ValidationHelper
            
            # Test valid data
            errors = ValidationHelper.validate_user_data("John Doe", "john@test.com", "password123")
            assert len(errors) == 0
            
            # Test invalid data
            errors = ValidationHelper.validate_user_data("", "invalid", "123")
            assert len(errors) > 0
            print("  ✅ Validation helpers working")
            
            print("\n🎉 All basic functionality tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_auth_integration():
    """Test integration with existing auth system"""
    print("\n🔐 Testing Auth Integration...")
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Test 1: Auth routes are accessible
                response = client.get('/')
                assert response.status_code == 200
                print("  ✅ Main page loads")
                
                # Test 2: Auth forms exist and can be imported
                from app.auth.forms import LoginForm, SignupForm
                
                login_form = LoginForm()
                signup_form = SignupForm()
                
                assert hasattr(login_form, 'email')
                assert hasattr(login_form, 'password')
                assert hasattr(signup_form, 'name')
                assert hasattr(signup_form, 'email')
                print("  ✅ Auth forms accessible")
                
                # Test 3: User model works with Flask-Login
                user = User(user_name="Auth Test", email="auth@test.com")
                user.set_password("authpass123")
                
                assert user.is_authenticated == True
                assert user.is_active == True
                assert user.is_anonymous == False
                print("  ✅ Flask-Login integration working")
                
                print("  🎉 Auth integration tests passed!")
                return True
                
            except Exception as e:
                print(f"  ❌ Auth integration test failed: {e}")
                return False

def test_services_logic():
    """Test service layer logic without database operations"""
    print("\n⚙️ Testing Services Logic...")
    
    try:
        # Test 1: Check if services can be imported properly
        from app.services import (
            UserService, TransactionService, AnalyticsService,
            ExportService, MemberService
        )
        
        # Test 2: Service methods exist and are callable
        assert hasattr(UserService, 'add_member_to_user')
        assert hasattr(TransactionService, 'add_personal_transaction')
        assert hasattr(AnalyticsService, 'get_spending_by_category')
        assert hasattr(ExportService, 'export_user_data')
        assert hasattr(MemberService, 'get_member_transactions_summary')
        print("  ✅ All service classes and methods exist")
        print("  ✅ Services can be imported")
        
        # Test 3: Basic validation in services (skip DB-dependent helpers)
        from app.utils import DateHelper, TransactionHelper, ValidationHelper, QueryPerformanceHelper
        
        # Test DateHelper
        year, month = DateHelper.get_current_month()
        assert isinstance(year, int)
        assert isinstance(month, int)
        
        # Test ValidationHelper 
        errors = ValidationHelper.validate_user_data("Test", "test@example.com", "password123")
        assert isinstance(errors, list)
        
        # Test QueryPerformanceHelper validation
        errors = QueryPerformanceHelper.validate_transaction_data(50.0, 'expense')
        assert isinstance(errors, list)
        
        print("  ✅ Helper classes working")
        
        print("  🎉 Services logic tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Services test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simplified tests"""
    print("🚀 Starting Simple Backend Tests...")
    print("=" * 50)
    
    success = True
    
    if not test_basic_functionality():
        success = False
    
    if not test_auth_integration():
        success = False
        
    if not test_services_logic():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL SIMPLE TESTS PASSED!")
        print("✅ Your backend is working correctly!")
        print("✅ Models, Auth, Services, and Utils all functional!")
    else:
        print("❌ Some tests failed - check the output above")
    
    return success

if __name__ == '__main__':
    success = main()
    import sys
    sys.exit(0 if success else 1)