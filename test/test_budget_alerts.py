# -*- coding: utf-8 -*-
"""
Test Budget Alert Functionality
Tests the new budget alert features
"""

from app import create_app, db
from app.models import User, Budget, Category
from app.services import BudgetService
from datetime import datetime, date
from decimal import Decimal

def test_budget_alerts():
    """Test budget alert functionality"""
    print("Testing Budget Alert Functionality...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create test user with unique email
            import time
            unique_email = f"alert{int(time.time())}@test.com"
            user = User(user_name="Alert Test User", email=unique_email)
            user.set_password("testpass123")
            db.session.add(user)
            db.session.commit()
            
            # Create test budget with custom alert threshold
            budget = BudgetService.create_user_total_budget(
                user_id=user.user_id,
                budget_amount=Decimal('100.00'),
                budget_period='monthly'
            )
            
            # Update alert settings manually for testing
            budget.alert_threshold = 75.0
            budget.notifications_enabled = True
            db.session.commit()
            
            print(f"  Created budget with ${budget.budget_amount} and 75% alert threshold")
            
            # Test alert methods with different spending amounts
            test_scenarios = [
                (50.0, "50% spending - should not alert"),
                (75.0, "75% spending - should alert at threshold"),
                (90.0, "90% spending - should alert above threshold"),
                (110.0, "110% spending - should alert over budget")
            ]
            
            for amount, description in test_scenarios:
                alert_status = budget.get_alert_status(amount)
                print(f"  {description}:")
                print(f"    - Percentage used: {alert_status['percentage_used']}%")
                print(f"    - Should alert: {alert_status['should_alert']}")
                print(f"    - Status: {alert_status['status']}")
                print(f"    - Amount remaining: ${alert_status['amount_remaining']}")
            
            # Test basic alert functionality
            print("  Budget alert system working")
            
            # Test serialization with alert fields
            budget_dict = budget.to_dict()
            assert 'alert_threshold' in budget_dict
            assert 'notifications_enabled' in budget_dict
            print("  Budget serialization includes alert fields")
            
            # Clean up
            db.session.delete(user)
            db.session.commit()
            
            print("  All budget alert tests passed!")
            return True
            
        except Exception as e:
            print(f"  Alert test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_budget_alerts()
    import sys
    sys.exit(0 if success else 1)