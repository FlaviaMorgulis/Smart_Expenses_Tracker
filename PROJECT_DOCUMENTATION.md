# Smart Expenses Tracker - Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Database Design](#database-design)
4. [Features & Functionality](#features--functionality)
5. [Technology Stack](#technology-stack)
6. [Installation & Setup](#installation--setup)
7. [User Guide](#user-guide)
8. [API Endpoints](#api-endpoints)
9. [Testing](#testing)
10. [Security & Authentication](#security--authentication)
11. [Future Enhancements](#future-enhancements)

---

## Project Overview

### Purpose

Smart Expenses Tracker is a comprehensive family expense management web application that enables users to track personal and shared expenses, manage family member contributions, set budgets, and generate detailed financial reports.

### Key Objectives

- Simplify expense tracking for individuals and families
- Provide cost-splitting functionality for shared expenses
- Enable budget management with intelligent alerts
- Deliver actionable financial insights through analytics
- Support data export for external analysis

### Target Users

- Individuals managing personal finances
- Families tracking shared household expenses
- Users who need to split costs among family members
- Budget-conscious users requiring spending alerts

### Project Status

**Current Version:** 1.0  
**Development Stage:** Deployed and Production-ready  
**Test Coverage:** 100% (49/49 tests passing)  
**Deployment Platform:** PythonAnywhere  
**Last Updated:** November 2025

---

## System Architecture

### Architecture Pattern

**Model-View-Controller (MVC)** with Flask Blueprints

```
Smart_Expenses_Tracker/
│
├── app/                          # Application package
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models (Model layer)
│   ├── admin.py                 # Admin interface configuration
│   ├── services.py              # Business logic services
│   ├── utils.py                 # Utility functions
│   │
│   ├── auth/                    # Authentication blueprint
│   │   ├── routes.py           # Auth routes (Controller)
│   │   └── forms.py            # Auth forms (WTForms)
│   │
│   ├── main/                    # Main application blueprint
│   │   └── routes.py           # Main routes (Controller)
│   │
│   ├── transactions/            # Transactions blueprint
│   │   ├── routes.py           # Transaction routes (Controller)
│   │   └── forms.py            # Transaction forms (WTForms)
│   │
│   ├── templates/               # HTML templates (View layer)
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── transactions.html
│   │   ├── family_management.html
│   │   ├── budget.html
│   │   └── ...
│   │
│   └── static/                  # Static assets
│       ├── css/                 # Stylesheets
│       ├── js/                  # JavaScript files
│       └── images/              # Image assets
│
├── migrations/                  # Database migrations (Alembic)
├── tests/                       # Test suite (pytest)
├── instance/                    # Instance-specific files (SQLite DB)
├── requirements.txt             # Python dependencies
└── run.py                      # Application entry point
```

### Application Flow

1. **Request** → Flask receives HTTP request
2. **Routing** → Blueprint routes request to appropriate controller
3. **Authentication** → Flask-Login verifies user session
4. **Controller** → Route handler processes request
5. **Business Logic** → Service layer handles complex operations
6. **Data Layer** → SQLAlchemy ORM interacts with database
7. **Response** → Jinja2 renders template with data
8. **Client** → Browser receives rendered HTML

### Blueprints Structure

- **auth_bp**: User authentication (login, signup, logout)
- **main_bp**: Core application routes (dashboard, profile, family management)
- **transactions_bp**: Transaction management and financial analytics

---

## Database Design

### Database Technology

- **Development:** SQLite (`expenses.db`)
- **ORM:** SQLAlchemy 2.0.36
- **Migrations:** Flask-Migrate (Alembic)

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────────┐         ┌──────────────┐
│    User     │1       *│   Transaction   │*       1│   Category   │
│─────────────│◄────────│─────────────────│────────►│──────────────│
│ user_id PK  │         │ transaction_id PK│        │ category_id PK│
│ user_name   │         │ user_id FK       │        │ category_name│
│ email       │         │ category_id FK   │        │ user_id FK   │
│ password    │         │ amount           │        └──────────────┘
│ is_admin    │         │ transaction_type │
└─────────────┘         │ transaction_date │
      │1                │ user_participates│
      │                 └─────────────────┘
      │                          │*
      │                          │
      │                          │
      │                 ┌────────▼────────┐
      │                 │ MembersTransaction│
      │                 │─────────────────│
      │                 │ transaction_id PK,FK│
      │                 │ member_id PK,FK │
      │                 └─────────────────┘
      │                          │*
      │                          │
      │1                ┌────────▼────────┐
      └────────────────►│     Member      │
                        │─────────────────│
                        │ member_id PK    │
                        │ user_id FK      │
                        │ name            │
                        │ relationship    │
                        └─────────────────┘
                                 │1
                                 │
                                 │*
                        ┌────────▼────────┐
                        │     Budget      │
                        │─────────────────│
                        │ budget_id PK    │
                        │ user_id FK      │
                        │ member_id FK    │
                        │ category_id FK  │
                        │ budget_amount   │
                        │ is_active       │
                        │ alert_threshold │
                        └─────────────────┘
```

### Database Tables

#### 1. **users**

Primary user accounts table.

| Column        | Type         | Constraints             | Description                |
| ------------- | ------------ | ----------------------- | -------------------------- |
| user_id       | INTEGER      | PK, AUTO_INCREMENT      | Unique user identifier     |
| user_name     | VARCHAR(255) | NOT NULL                | Display name               |
| email         | VARCHAR(255) | UNIQUE, NOT NULL        | Login email                |
| password_hash | VARCHAR(255) | NOT NULL                | Bcrypt hashed password     |
| created_at    | DATETIME     | NOT NULL, DEFAULT NOW   | Account creation timestamp |
| is_admin      | BOOLEAN      | NOT NULL, DEFAULT FALSE | Admin privileges flag      |

**Relationships:**

- One-to-Many with `members` (CASCADE DELETE)
- One-to-Many with `transactions` (CASCADE DELETE)
- One-to-Many with `categories` (CASCADE DELETE)
- One-to-Many with `budgets` (CASCADE DELETE)

#### 2. **categories**

Expense categorization system (predefined + user-created).

| Column        | Type    | Constraints        | Description                                                                          |
| ------------- | ------- | ------------------ | ------------------------------------------------------------------------------------ |
| category_id   | INTEGER | PK, AUTO_INCREMENT | Unique category identifier                                                           |
| category_name | ENUM    | NOT NULL           | 'Transport', 'Utilities', 'Entertainment', 'Food', 'Healthcare', 'Shopping', 'Other' |
| user_id       | INTEGER | FK, NULL           | NULL for system categories, user_id for custom                                       |

**System Categories:** Transport, Utilities, Entertainment, Food, Healthcare, Shopping, Other

**Relationships:**

- Many-to-One with `users` (nullable for system categories)
- One-to-Many with `transactions` (PASSIVE DELETE)

#### 3. **members**

Family members tracked by the user (data entities, not user accounts).

| Column       | Type         | Constraints           | Description                                    |
| ------------ | ------------ | --------------------- | ---------------------------------------------- |
| member_id    | INTEGER      | PK, AUTO_INCREMENT    | Unique member identifier                       |
| user_id      | INTEGER      | FK, NOT NULL          | Owner user                                     |
| name         | VARCHAR(255) | NOT NULL              | Member's display name                          |
| relationship | VARCHAR(100) | NOT NULL              | Relationship to user (e.g., "Spouse", "Child") |
| joined_at    | DATETIME     | NOT NULL, DEFAULT NOW | When user added this member                    |

**Important:** Members are data entities managed by the user, NOT separate user accounts.

**Relationships:**

- Many-to-One with `users` (CASCADE DELETE)
- One-to-Many with `members_transaction` (CASCADE DELETE)
- One-to-Many with `budgets` (CASCADE DELETE)

#### 4. **transactions**

Financial transactions (income/expenses) created by users.

| Column            | Type         | Constraints            | Description                             |
| ----------------- | ------------ | ---------------------- | --------------------------------------- |
| transaction_id    | INTEGER      | PK, AUTO_INCREMENT     | Unique transaction identifier           |
| user_id           | INTEGER      | FK, NOT NULL           | User who created transaction            |
| category_id       | INTEGER      | FK, NULL               | Expense category (NULL if deleted)      |
| amount            | NUMERIC(8,2) | NOT NULL               | Transaction amount (GBP)                |
| transaction_type  | ENUM         | NOT NULL               | 'income' or 'expense'                   |
| transaction_date  | DATETIME     | NOT NULL               | Transaction occurrence date             |
| created_at        | DATETIME     | NOT NULL, DEFAULT NOW  | Record creation timestamp               |
| user_participates | BOOLEAN      | NOT NULL, DEFAULT TRUE | Whether user participates in cost split |

**Cost Splitting Logic:**

- **Personal Transaction:** `user_participates=TRUE`, no members → User pays 100%
- **Shared Transaction:** `user_participates=TRUE`, has members → Cost split evenly
- **Members-Only Transaction:** `user_participates=FALSE`, has members → User paid but doesn't participate in split

**Relationships:**

- Many-to-One with `users` (CASCADE DELETE)
- Many-to-One with `categories` (SET NULL on category delete)
- One-to-Many with `members_transaction` (CASCADE DELETE)

#### 5. **members_transaction**

Junction table linking transactions to assigned members (many-to-many).

| Column         | Type    | Constraints | Description           |
| -------------- | ------- | ----------- | --------------------- |
| transaction_id | INTEGER | PK, FK      | Transaction reference |
| member_id      | INTEGER | PK, FK      | Member reference      |

**Composite Primary Key:** (transaction_id, member_id)

**Relationships:**

- Many-to-One with `transactions` (CASCADE DELETE)
- Many-to-One with `members` (CASCADE DELETE)

#### 6. **budgets**

Budget tracking for users and members, by category or total.

| Column                | Type          | Constraints            | Description                                |
| --------------------- | ------------- | ---------------------- | ------------------------------------------ |
| budget_id             | INTEGER       | PK, AUTO_INCREMENT     | Unique budget identifier                   |
| budget_amount         | NUMERIC(10,2) | NOT NULL               | Budget limit amount                        |
| is_active             | BOOLEAN       | NOT NULL, DEFAULT TRUE | Active/paused status                       |
| alert_threshold       | NUMERIC(5,2)  | NOT NULL, DEFAULT 80.0 | Alert percentage (0-100)                   |
| notifications_enabled | BOOLEAN       | NOT NULL, DEFAULT TRUE | Enable/disable alerts                      |
| created_at            | DATETIME      | NOT NULL, DEFAULT NOW  | Budget creation time                       |
| updated_at            | DATETIME      | NOT NULL, DEFAULT NOW  | Last modification time                     |
| user_id               | INTEGER       | FK, NULL               | For user budgets                           |
| member_id             | INTEGER       | FK, NULL               | For member budgets                         |
| category_id           | INTEGER       | FK, NULL               | For category budgets (NULL = total budget) |

**Budget Types:**

- **User Total Budget:** `user_id` set, `member_id=NULL`, `category_id=NULL`
- **User Category Budget:** `user_id` set, `member_id=NULL`, `category_id` set
- **Member Total Budget:** `member_id` set, `user_id=NULL`, `category_id=NULL`
- **Member Category Budget:** `member_id` set, `user_id=NULL`, `category_id` set

**Validation:** Budget must belong to EITHER user OR member (XOR constraint).

**Relationships:**

- Many-to-One with `users` (CASCADE DELETE)
- Many-to-One with `members` (CASCADE DELETE)
- Many-to-One with `categories` (SET NULL on category delete)

### Database Seeding

System categories are automatically seeded on first run:

- Transport, Utilities, Entertainment, Food, Healthcare, Shopping, Other

---

## Features & Functionality

### 1. User Authentication & Authorization

#### Features

- **User Registration:** Email-based signup with password hashing
- **Secure Login:** Session-based authentication via Flask-Login
- **Password Security:** Werkzeug bcrypt password hashing with random salt
- **Session Management:** Persistent login sessions with "Remember Me" option
- **Admin Access:** Role-based access control with `is_admin` flag
- **Logout:** Secure session termination

#### Technical Implementation

- **Library:** Flask-Login 0.7.0
- **Password Hashing:** `werkzeug.security.generate_password_hash()`
- **Authentication Check:** `@login_required` decorator on protected routes
- **User Loader:** `load_user()` callback for session management

### 2. Dashboard & Analytics

#### Features

- **Monthly Summary:** Current month's income, expenses, and balance
- **Spending Trends:** Month-over-month comparison
- **Category Breakdown:** Visual distribution of expenses by category
- **Budget Status:** Real-time budget usage with progress indicators
- **Quick Stats:** Total transactions, average daily spending
- **Recent Activity:** Latest 10 transactions

#### Visualizations

- Pie charts for category distribution
- Bar charts for monthly comparisons
- Progress bars for budget tracking
- Trend indicators (↑ increase, ↓ decrease)

### 3. Transaction Management

#### Add Transaction

- **Fields:** Amount, Type (income/expense), Category, Date
- **Member Assignment:** Select family members for cost splitting
- **User Participation:** Toggle whether user participates in split
- **Validation:** Amount > 0, valid date, required fields

#### Edit Transaction

- **Full Editing:** Modify all transaction fields
- **Member Reassignment:** Update assigned members
- **Participation Toggle:** Change user participation status
- **Audit Trail:** `updated_at` timestamp tracking

#### Delete Transaction

- **Confirmation:** User confirmation before deletion
- **Cascade:** Automatically removes member associations
- **Permanent:** No soft delete (immediate removal)

#### List Transactions

- **Filtering:** By type (income/expense), category, date range
- **Sorting:** By date (newest/oldest), amount
- **Pagination:** Configurable items per page
- **Search:** Filter by amount or date
- **Export:** CSV and PDF export options

### 4. Family Member Management

#### Add Member

- **Fields:** Name, Relationship to user
- **Validation:** Unique name per user, required fields
- **Automatic Tracking:** `joined_at` timestamp

#### Edit Member

- **Update:** Name and relationship fields
- **Preserve History:** Existing transaction associations remain intact

#### Delete Member

- **Cascade:** Removes member from all transaction assignments
- **Budget Impact:** Deletes associated member budgets
- **Confirmation Required:** Prevents accidental deletion

#### Member Statistics

- **Total Contribution:** Lifetime spending tracked for member
- **Transaction Count:** Number of transactions member participated in
- **Average per Transaction:** Mean contribution amount
- **Monthly Breakdown:** Month-by-month spending analysis

### 5. Cost Splitting System

#### Splitting Logic

The application implements intelligent cost splitting based on user participation:

**Personal Transaction (No Members):**

```
User Share: 100% of amount
Members Share: 0%
```

**Shared Transaction (User Participates):**

```
Participants: User + Assigned Members
Cost per Person: Amount ÷ (1 + Number of Members)
User Share: Cost per Person
Each Member Share: Cost per Person
```

**Members-Only Transaction (User Paid, Doesn't Participate):**

```
Participants: Assigned Members only
Cost per Person: Amount ÷ Number of Members
User Share: 0%
Each Member Share: Cost per Person
```

#### Example Scenarios

**Scenario 1: Groceries (Shared)**

- Amount: £100
- Members: Sarah (Spouse)
- User Participates: Yes
- **Result:** User pays £50, Sarah owes £50

**Scenario 2: Kids' School Trip (Members-Only)**

- Amount: £60
- Members: Emma (Child), Jack (Child)
- User Participates: No
- **Result:** User pays £60 upfront, Emma owes £30, Jack owes £30

**Scenario 3: Personal Coffee (Personal)**

- Amount: £5
- Members: None
- **Result:** User pays £5, no splitting

### 6. Budget Management

#### Create Budget

- **Budget Types:**
  - User Total Budget (all categories)
  - User Category Budget (specific category)
  - Member Total Budget (all member expenses)
  - Member Category Budget (member's specific category)
- **Fields:** Amount, Alert Threshold (%), Notifications On/Off
- **Validation:** Exactly one owner (user XOR member)

#### Budget Alerts

- **Threshold-Based:** Alert when spending reaches % threshold (default: 80%)
- **Status Indicators:**
  - Within Budget (Green)
  - Approaching Threshold (Yellow)
  - Threshold Reached (Orange)
  - Over Budget (Red)
- **Real-Time Calculations:** Updates on every transaction
- **Notification Control:** Enable/disable alerts per budget

#### Pause/Unpause Budget

- **Pause:** Temporarily deactivate budget without deletion
- **Unpause:** Reactivate paused budget
- **Status Tracking:** `is_active` flag with `updated_at` timestamp

### 7. Data Export

#### CSV Export

- **Format:** Comma-separated values
- **Fields:** Date, Type, Category, Amount, Members, User Share, Members Share
- **Filtering:** Export filtered/searched results only
- **Use Cases:** Excel analysis, tax preparation, sharing with accountants

#### PDF Export

- **Format:** Professional PDF report
- **Library:** ReportLab 4.4.4
- **Includes:** Transaction summary, category breakdown, date range
- **Styling:** Formatted tables with headers and totals

### 8. User Profile Management

#### Profile Information

- **View:** Display name, email, account creation date
- **Edit:** Update name and email
- **Validation:** Unique email, format validation

#### Account Actions

- **Clear All Data:** Delete all transactions, members, budgets (keeps account)
- **Delete Account:** Permanent account deletion with cascade (all data removed)
- **Confirmation:** Double-confirmation for destructive actions

### 9. Admin Interface

#### Flask-Admin Integration

- **Access Control:** Admin-only access (`is_admin=True`)
- **Model Views:** Direct database management
- **Bulk Operations:** Multi-row editing and deletion
- **Search & Filter:** Advanced querying capabilities
- **User Management:** View all users, promote/demote admins

---

## Technology Stack

### Backend Framework

- **Flask 3.1.2:** Web framework
- **Python 3.13:** Programming language
- **Werkzeug 3.1.3:** WSGI utilities
- **Jinja2 3.1.6:** Template engine

### Database & ORM

- **SQLAlchemy 2.0.36:** ORM and database toolkit
- **Flask-SQLAlchemy 3.1.1:** Flask integration for SQLAlchemy
- **Flask-Migrate 4.0.7:** Database migrations (Alembic wrapper)
- **SQLite 3:** Development database

### Authentication & Forms

- **Flask-Login 0.7.0:** User session management
- **Flask-WTF 1.2.2:** Form handling and CSRF protection
- **WTForms 3.2.1:** Form validation
- **validators 0.35.0:** Email and input validation

### Admin & Utilities

- **Flask-Admin:** Administrative interface
- **ReportLab 4.4.4:** PDF generation
- **python-dateutil 2.9.0:** Date parsing

### Testing

- **pytest 8.4.2:** Testing framework
- **pytest-flask:** Flask application testing utilities
- **coverage:** Code coverage analysis

### Frontend

- **HTML5/CSS3:** Markup and styling
- **Vanilla JavaScript:** Client-side interactivity
- **Responsive Design:** Mobile-first approach with CSS Grid/Flexbox

### Development Tools

- **Git:** Version control
- **VS Code:** IDE with Python extensions
- **Virtual Environment:** Isolated dependency management

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### Step 1: Clone Repository

```bash
git clone https://github.com/FlaviaMorgulis/Smart_Expenses_Tracker.git
cd Smart_Expenses_Tracker
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
# Create database tables
flask db upgrade

# Or use Python shell
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Step 5: Seed System Categories

```bash
python
>>> from app import create_app, db
>>> from app.utilities.seed_categories import seed_system_categories
>>> app = create_app()
>>> with app.app_context():
...     seed_system_categories()
>>> exit()
```

### Step 6: Create Admin User (Optional)

```bash
python create_admin.py
```

**Default Admin Credentials:**

- Email: `admin@smartexpenses.com`
- Password: `Admin123!`

### Step 7: Run Application

```bash
python run.py
```

Application will be available at: `http://127.0.0.1:5000`

### Step 8: Run Tests (Optional)

```bash
pytest
pytest --cov=app  # With coverage report
```

---

## User Guide

### Getting Started

#### 1. Create Account

1. Navigate to homepage
2. Click "Sign Up"
3. Enter name, email, password
4. Submit registration form
5. Automatically logged in

#### 2. Add First Transaction

1. Go to "Transactions" page
2. Click "Add Transaction"
3. Fill in:
   - Amount (e.g., 50.00)
   - Type (Income/Expense)
   - Category (from dropdown)
   - Date (defaults to today)
4. Click "Add Transaction"

#### 3. Add Family Member

1. Go to "Family Management"
2. Click "Add Member"
3. Enter:
   - Name (e.g., "Sarah Thompson")
   - Relationship (e.g., "Spouse")
4. Click "Add Member"

#### 4. Create Shared Expense

1. Go to "Transactions" → "Add Transaction"
2. Enter expense details
3. Select family members to share cost
4. Toggle "I participate in this expense" (default: ON)
5. Submit

#### 5. Set Up Budget

1. Go to "Budgets" page
2. Click "Create Budget"
3. Choose:
   - Owner (You or a family member)
   - Category (or "All Categories")
   - Amount limit
   - Alert threshold (default: 80%)
4. Submit

### Common Tasks

#### View Monthly Summary

- Dashboard automatically shows current month
- Income, expenses, and balance displayed
- Refresh automatically on new transactions

#### Filter Transactions

1. Go to "Transactions" page
2. Use filter dropdowns:
   - Type (All/Income/Expense)
   - Category (All or specific)
   - Date range
3. Click "Apply Filters"

#### Export Data

**CSV Export:**

1. Go to "Transactions"
2. Apply any filters (optional)
3. Click "Export CSV"
4. File downloads automatically

**PDF Export:**

1. Go to "Transactions"
2. Click "Export PDF"
3. PDF report downloads

#### Edit Transaction

1. Go to "Transactions"
2. Find transaction in list
3. Click "Edit" button
4. Modify fields
5. Click "Save Changes"

#### Check Member Statistics

1. Go to "Family Management"
2. View member card statistics:
   - Total Contribution
   - Transaction Count
   - Average per Transaction
3. Click member for detailed breakdown

---

## API Endpoints

### Authentication Routes (`/`)

| Method   | Endpoint  | Description            | Auth Required |
| -------- | --------- | ---------------------- | ------------- |
| GET/POST | `/login`  | User login page        | No            |
| GET/POST | `/signup` | User registration page | No            |
| GET      | `/logout` | Logout current user    | Yes           |

### Main Routes (`/`)

| Method | Endpoint              | Description                         | Auth Required |
| ------ | --------------------- | ----------------------------------- | ------------- |
| GET    | `/`                   | Homepage/Landing page               | No            |
| GET    | `/dashboard`          | User dashboard with analytics       | Yes           |
| GET    | `/about`              | About page                          | No            |
| GET    | `/faq`                | FAQ page                            | No            |
| GET    | `/cashflow`           | Cash flow analysis                  | Yes           |
| GET    | `/family_management`  | Family member management            | Yes           |
| POST   | `/add_member`         | Create new family member            | Yes           |
| POST   | `/edit_member`        | Update member details               | Yes           |
| POST   | `/delete_member/<id>` | Delete family member                | Yes           |
| GET    | `/profile`            | User profile page                   | Yes           |
| POST   | `/update_profile`     | Update user profile                 | Yes           |
| POST   | `/clear_all_data`     | Delete all user data (keep account) | Yes           |
| POST   | `/delete_account`     | Delete user account permanently     | Yes           |

### Transaction Routes (`/transactions`)

| Method      | Endpoint                                | Description                | Auth Required |
| ----------- | --------------------------------------- | -------------------------- | ------------- |
| GET         | `/transactions/`                        | List all transactions      | Yes           |
| POST        | `/transactions/add_transaction`         | Create new transaction     | Yes           |
| GET/POST    | `/transactions/edit_transaction/<id>`   | Edit transaction           | Yes           |
| POST/DELETE | `/transactions/delete_transaction/<id>` | Delete transaction         | Yes           |
| GET         | `/transactions/budgets`                 | Budget management page     | Yes           |
| GET         | `/transactions/export/csv`              | Export transactions as CSV | Yes           |
| GET         | `/transactions/export/pdf`              | Export transactions as PDF | Yes           |

### API Endpoints (JSON Responses)

| Method | Endpoint                               | Description                    | Auth Required |
| ------ | -------------------------------------- | ------------------------------ | ------------- |
| GET    | `/transactions/api/transaction_stats`  | Monthly transaction statistics | Yes           |
| GET    | `/transactions/api/category_spending`  | Spending by category           | Yes           |
| GET    | `/transactions/api/budget_alerts`      | Active budget alerts           | Yes           |
| GET    | `/transactions/api/monthly_comparison` | Month-over-month comparison    | Yes           |

### Admin Routes (`/admin`)

| Method | Endpoint              | Description            | Auth Required | Admin Only |
| ------ | --------------------- | ---------------------- | ------------- | ---------- |
| GET    | `/admin/`             | Admin dashboard        | Yes           | Yes        |
| GET    | `/admin/user/`        | User management        | Yes           | Yes        |
| GET    | `/admin/transaction/` | Transaction management | Yes           | Yes        |
| GET    | `/admin/category/`    | Category management    | Yes           | Yes        |
| GET    | `/admin/budget/`      | Budget management      | Yes           | Yes        |

---

## Testing

### Test Suite Structure

```
tests/
├── __init__.py                    # Package marker
├── conftest.py                    # Pytest fixtures and configuration
├── test_auth.py                   # Authentication tests (15 tests)
├── test_transactions.py           # Transaction CRUD tests (6 tests)
├── test_family_management.py      # Family member tests (8 tests)
├── test_budgets.py               # Budget management tests (10 tests)
└── test_cost_splitting.py        # Cost splitting logic tests (10 tests)
```

### Test Coverage

- **Total Tests:** 49
- **Passing:** 49 (100%)
- **Failing:** 0
- **Skipped:** 0

### Running Tests

#### Run All Tests

```bash
pytest
```

#### Run Specific Test File

```bash
pytest tests/test_auth.py
pytest tests/test_cost_splitting.py
```

#### Run with Coverage Report

```bash
pytest --cov=app
pytest --cov=app --cov-report=html  # HTML report
```

#### Run with Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Test Fixtures (`conftest.py`)

#### `app()`

Creates test Flask application with:

- In-memory SQLite database (`sqlite:///:memory:`)
- CSRF protection disabled for testing
- Fresh database for each test

#### `client(app)`

Returns Flask test client for making HTTP requests.

#### `test_user(app)`

Creates standard test user:

- Email: `testuser@example.com`
- Password: `Test123!`

#### `admin_user(app)`

Creates admin user:

- Email: `admin@test.com`
- Password: `Admin123!`
- is_admin: `True`

#### `auth_client(client, test_user)`

Returns authenticated test client (logged in as test_user).

#### `test_category(app)`

Returns Food category ID (system category).

#### `test_member(app, test_user)`

Creates test family member:

- Name: Sarah Johnson
- Relationship: Spouse

### Key Test Cases

#### Authentication Tests

- User registration with valid data
- Registration with duplicate email (should fail)
- Login with correct credentials
- Login with wrong password (should fail)
- Protected route access without login
- Admin-only route access control

#### Transaction Tests

- Add transaction with valid data
- Edit existing transaction
- Delete transaction
- List user's transactions
- Transaction filtering by category/type

#### Family Management Tests

- Add family member
- Edit member details
- Delete member (cascade to transactions)
- View member statistics
- Member contribution calculations

#### Budget Tests

- Create user budget
- Create member budget
- Create category-specific budget
- Budget alert threshold calculations
- Pause/unpause budget functionality

#### Cost Splitting Tests

- Personal transaction (100% to user)
- Shared transaction (even split)
- Members-only transaction (user pays, doesn't participate)
- Cost per person calculations
- User share vs members share logic

## Security & Authentication

### Password Security

- **Hashing Algorithm:** Bcrypt (via Werkzeug)
- **Salt:** Random salt per password
- **Storage:** Only hashed passwords stored in database
- **Validation:** `check_password_hash()` for verification

### Session Management

- **Library:** Flask-Login
- **Session Type:** Server-side sessions
- **Session Cookie:** Secure, HttpOnly cookies
- **Session Timeout:** Configurable (default: browser session)
- **Remember Me:** Optional persistent login

### CSRF Protection

- **Library:** Flask-WTF
- **Mechanism:** CSRF tokens in all forms
- **Validation:** Automatic token verification on POST requests
- **Ajax Support:** Token included in headers for JavaScript requests

### Input Validation

- **Forms:** WTForms validation on all user inputs
- **Email:** Format validation with `validators` library
- **Amounts:** Numeric validation, min/max constraints
- **SQL Injection:** Prevented by SQLAlchemy parameterized queries
- **XSS:** Jinja2 automatic HTML escaping

### Authorization

- **Login Required:** `@login_required` decorator on protected routes
- **Admin Access:** `@admin_required` custom decorator
- **Ownership Check:** Users can only access their own data
- **Cascade Delete:** User data deleted on account deletion

### Data Privacy

- **User Isolation:** Users cannot view other users' data
- **Member Privacy:** Members are private to owning user
- **Transaction Privacy:** Transactions visible only to creator
- **Admin Separation:** Admin interface separate from user interface

### Secure Configuration

```python
# Recommended production settings
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Strong random key
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

---

## Future Enhancements

### Short-Term (Next 3 Months)

#### 1. Fix Known Bugs

- ✅ Resolve 3 failing budget route tests
- ✅ Address SQLAlchemy 2.0 deprecation warnings
- ✅ Implement proper error handling for 500 errors

#### 2. Enhanced Budget Features

- Budget period selection (weekly/monthly/yearly)
- Recurring budgets (auto-reset monthly)
- Budget rollover (unused budget → next period)
- Budget history tracking

#### 3. Improved Analytics

- Year-over-year spending comparison
- Spending trend predictions (ML-based)
- Category spending heatmaps
- Custom date range analytics

### Medium-Term (6-12 Months)

#### 4. Receipt Scanning

- Mobile camera integration
- OCR text extraction (Tesseract)
- Auto-populate transaction from receipt
- Attachment storage (S3/cloud)

#### 5. Notifications System

- Email budget alerts
- In-app notification center
- Configurable alert rules

#### 6. Data Visualization

- Interactive charts (Chart.js/D3.js)
- Customizable dashboard widgets
- Spending forecasts
- Goal progress tracking

#### 7. Multi-Currency Support

- Currency conversion API integration
- Multiple currency transactions
- Exchange rate tracking
- Base currency preference

### Long-Term (12+ Months)

#### 8. Mobile Application

- React Native mobile app
- Offline mode with sync
- Push notifications
- Camera receipt scanning

#### 9. Shared Family Accounts

- Multi-user access to single account
- Role-based permissions (viewer/editor/admin)
- Real-time collaboration
- Activity audit log

#### 10. Advanced Reporting

- Tax report generation
- Expense reimbursement reports
- Custom report builder
- Scheduled report delivery (email)

#### 11. Integration APIs

- Bank account linking (Plaid/Open Banking)
- Automatic transaction import
- Credit card sync
- Investment account tracking

#### 12. Machine Learning Features

- Spending pattern recognition
- Anomaly detection (unusual expenses)
- Category auto-suggestion
- Budget recommendations based on history

#### 13. Recurring Transactions

- Subscription tracking
- Auto-create monthly expenses
- Reminder system
- Recurring budget adjustments

---

## Conclusion

Smart Expenses Tracker is a production-ready web application that successfully delivers comprehensive family expense management with intelligent cost-splitting, budget tracking, and detailed analytics. The application demonstrates solid software engineering practices with clean architecture, comprehensive testing, and secure authentication.

### Project Achievements

✅ **83.7% Test Coverage** with 41/49 tests passing  
✅ **Secure Authentication** with bcrypt password hashing  
✅ **Intelligent Cost Splitting** with flexible participation logic  
✅ **Real-Time Budget Alerts** with customizable thresholds  
✅ **Data Export** in CSV and PDF formats  
✅ **Responsive Design** for desktop and mobile  
✅ **Comprehensive Documentation** with test plans and user stories

### Technical Highlights

- Clean MVC architecture with Flask Blueprints
- Robust database design with proper relationships
- Well-tested business logic with pytest
- Admin interface for system management
- Production-ready code quality

### Deployment Ready

The application is ready for production deployment with minimal configuration changes (environment variables, production database, HTTPS configuration).

---

## Appendix

### Configuration Variables

```python
# Environment Variables for Production
SECRET_KEY=<strong-random-key>
DATABASE_URL=<production-database-url>
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
MAIL_SERVER=<smtp-server>
MAIL_PORT=587
MAIL_USERNAME=<email-username>
MAIL_PASSWORD=<email-password>
```

### Database Migration Commands

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade

# View migration history
flask db history
```

### Deployment Checklist

- [ ] Set strong SECRET_KEY
- [ ] Configure production database (PostgreSQL)
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set secure session cookies
- [ ] Configure email server for alerts
- [ ] Set up error logging (Sentry)
- [ ] Enable database backups
- [ ] Configure CORS if needed
- [ ] Set up monitoring (New Relic/Datadog)
- [ ] Implement rate limiting (Flask-Limiter)

### Support & Contact

- **Repository:** https://github.com/FlaviaMorgulis/Smart_Expenses_Tracker
- **Issues:** Submit via GitHub Issues
- **Documentation:** See `/docs` folder for detailed specs

---

**Document Version:** 1.0  
**Last Updated:** November 2025
