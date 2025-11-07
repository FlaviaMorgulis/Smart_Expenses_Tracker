from app import create_app, db
from app.models import User, Transaction, Category, Member, Budget
from decimal import Decimal
from datetime import datetime, timedelta
import random

app = create_app()

def create_sample_data():
    with app.app_context():
        print("🔄 Creating sample data for admin interface...")
        
        # Create some test users
        users = []
        for i in range(3):
            user = User(
                user_name=f'Sample User {i+1}',
                email=f'sampleuser{i+1}@example.com'
            )
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # Create categories if they don't exist
        categories = []
        category_names = ['Food', 'Transport', 'Entertainment', 'Utilities', 'Healthcare']
        for cat_name in category_names:
            category = Category.query.filter_by(category_name=cat_name, user_id=None).first()
            if not category:
                category = Category(category_name=cat_name, user_id=None)
                db.session.add(category)
            categories.append(category)
        
        db.session.commit()
        
        # Create members for users
        members = []
        relationships = ['spouse', 'child', 'parent']
        for i, user in enumerate(users):
            member = Member(
                user_id=user.user_id,
                name=f'Family Member {i+1}',
                relationship=relationships[i % len(relationships)]
            )
            members.append(member)
            db.session.add(member)
        
        db.session.commit()
        
        # Create transactions
        transactions = []
        for i in range(15):  # Create 15 sample transactions
            user = random.choice(users)
            category = random.choice(categories)
            amount = round(random.uniform(10.0, 200.0), 2)
            
            transaction = Transaction(
                user_id=user.user_id,
                category_id=category.category_id,
                amount=Decimal(str(amount)),
                transaction_type=random.choice(['income', 'expense']),
                transaction_date=datetime.now() - timedelta(days=random.randint(0, 30)),
                description=f'Sample transaction {i+1}'
            )
            transactions.append(transaction)
            db.session.add(transaction)
        
        # Create budgets
        budgets = []
        for user in users:
            for category in categories[:3]:  # Create budget for first 3 categories
                budget = Budget(
                    user_id=user.user_id,
                    category_id=category.category_id,
                    budget_amount=Decimal(str(random.randint(200, 800))),
                    budget_period='monthly',
                    is_active=True
                )
                budgets.append(budget)
                db.session.add(budget)
        
        db.session.commit()
        
        print("✅ Sample data created successfully!")
        print(f"📊 Created:")
        print(f"   - {len(users)} sample users")
        print(f"   - {len(categories)} categories")
        print(f"   - {len(members)} family members")
        print(f"   - {len(transactions)} transactions")
        print(f"   - {len(budgets)} budgets")
        print("\n🔗 Now go to http://127.0.0.1:5000/admin/ to see the data!")

if __name__ == '__main__':
    create_sample_data()