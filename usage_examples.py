# usage_examples.py - Examples of how to use the new service architecture

from app.models import User, Member, Transaction, Category
from app.services import UserService, TransactionService, AnalyticsService, ExportService, MemberService
from app.utils import initialize_categories, ValidationHelper
from datetime import datetime

# Example 1: User Registration and Authentication
def example_user_registration():
    """Example of user registration with validation"""
    
    # Validate user data first
    errors = ValidationHelper.validate_user_data("John Doe", "john@example.com", "password123")
    if errors:
        return {"errors": errors}
    
    # Create new user (using clean model)
    user = User(
        user_name="John Doe",
        email="john@example.com"
    )
    user.set_password("password123")  # Model handles password hashing
    
    db.session.add(user)
    db.session.commit()
    
    return {"success": True, "user": user}

# Example 2: Using Services for Business Logic  
def example_transaction_management():
    """Example of using services for transaction operations"""
    
    # Get user (using clean model)
    user = User.query.filter_by(email="john@example.com").first()
    
    # Add a personal transaction (using service)
    transaction = TransactionService.add_personal_transaction(
        user=user,
        amount=50.00,
        transaction_type='expense',
        category_id=1,
        transaction_date=datetime.now()
    )
    
    # Add a member first (using service)
    member = UserService.add_member_to_user(
        user=user,
        name="Jane Doe",
        relationship="spouse"
    )
    
    # Add a member transaction (using service)
    member_transaction = TransactionService.add_member_transaction(
        user=user,
        member_id=member.member_id,
        amount=75.00,
        transaction_type='expense',
        category_id=2
    )
    
    return {
        "personal_transaction": transaction,
        "member_transaction": member_transaction
    }

# Example 3: Analytics and Reporting
def example_analytics():
    """Example of using analytics service"""
    
    user = User.query.filter_by(email="john@example.com").first()
    
    # Get spending by category (using service)
    spending_breakdown = AnalyticsService.get_spending_by_category(
        user=user,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    
    # Get monthly summary (using service)
    monthly_summary = AnalyticsService.get_monthly_summary(
        user=user,
        year=2024,
        month=10
    )
    
    return {
        "spending_breakdown": spending_breakdown,
        "monthly_summary": monthly_summary
    }

# Example 4: Data Export
def example_data_export():
    """Example of using export service"""
    
    user = User.query.filter_by(email="john@example.com").first()
    
    # Export user data (using service)
    export_data = ExportService.export_user_data(
        user=user,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    
    return export_data

# Example 5: Member Management
def example_member_management():
    """Example of member operations"""
    
    user = User.query.filter_by(email="john@example.com").first()
    member = user.members[0]  # Get first member
    
    # Get member transaction summary (using service)
    member_summary = MemberService.get_member_transactions_summary(
        member_id=member.member_id
    )
    
    # Update member info (using clean model method)
    member.update_info(name="Jane Smith", relationship="wife")
    
    return {
        "member_summary": member_summary,
        "updated_member": member
    }

# Example 6: Using Route with Services (how routes.py would look)
def example_route_usage():
    """Example of how to use services in Flask routes"""
    
    from flask import request, jsonify
    
    # Example route for adding transaction
    @app.route('/add_transaction', methods=['POST'])
    def add_transaction():
        data = request.get_json()
        
        # Validate data
        errors = ValidationHelper.validate_transaction_data(
            amount=data.get('amount'),
            transaction_type=data.get('type'),
            category_id=data.get('category_id')
        )
        
        if errors:
            return jsonify({"errors": errors}), 400
        
        # Get current user (assume authentication is handled)
        user = current_user
        
        # Use service to add transaction
        if data.get('member_id'):
            transaction = TransactionService.add_member_transaction(
                user=user,
                member_id=data['member_id'],
                amount=data['amount'],
                transaction_type=data['type'],
                category_id=data['category_id']
            )
        else:
            transaction = TransactionService.add_personal_transaction(
                user=user,
                amount=data['amount'],
                transaction_type=data['type'],
                category_id=data['category_id']
            )
        
        return jsonify({
            "success": True,
            "transaction": transaction.to_dict()  # Model handles serialization
        })

# Example 7: Initialization 
def example_app_initialization():
    """Example of app initialization with utils"""
    
    # Initialize categories (using utils)
    initialize_categories()
    
    print("Categories initialized successfully!")

if __name__ == "__main__":
    print("These are usage examples for the new service architecture")
    print("Import these functions in your actual application code")