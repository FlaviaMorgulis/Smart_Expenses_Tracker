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

Smart Expenses Tracker is a comprehensive family expense management web application built with Flask 3.1.2 and Python 3.13.

**For project goals, user stories, and design philosophy**, see [README.md](README.md).

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
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── app/
│   ├── __init__.py            # App factory, extensions initialization
│   ├── models.py              # SQLAlchemy models (User, Transaction, Member, Budget, Category)
│   ├── services.py            # Business logic (cost splitting, budget calculations)
│   ├── utils.py               # Helper functions
│   ├── admin.py               # Admin user management
│   ├── auth/                  # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py          # Login, register, logout routes
│   │   └── forms.py           # WTForms for authentication
│   ├── main/                  # Main application blueprint
│   │   ├── __init__.py
│   │   └── routes.py          # Dashboard, profile routes
│   ├── transactions/          # Transaction management blueprint
│   │   ├── __init__.py
│   │   ├── routes.py          # CRUD operations for transactions
│   │   └── forms.py           # Transaction forms
│   ├── static/
│   │   ├── css/               # Stylesheets (style.css, budget.css, etc.)
│   │   ├── js/                # JavaScript files (script.js, members.js)
│   │   └── images/            # Static images
│   ├── templates/             # Jinja2 templates
│   │   ├── base.html          # Base template with navigation
│   │   ├── index.html         # Landing page
│   │   ├── dashboard.html     # Main dashboard
│   │   ├── transactions.html  # Transaction list
│   │   ├── edit_transaction.html # Edit transaction form
│   │   ├── budget.html        # Budget management
│   │   ├── family_management.html # Family members
│   │   ├── cashflow.html      # Cash flow analysis
│   │   ├── about.html         # About page
│   │   └── faq.html           # FAQ page
│   └── utilities/
│       └── seed_categories.py # Database seeding script
├── migrations/                 # Flask-Migrate database migrations
├── instance/
│   └── expenses.db            # SQLite database (dev)
└── tests/                     # pytest test suite
    ├── conftest.py            # Test fixtures
    ├── test_auth.py           # Authentication tests
    ├── test_family_management.py # Family management tests
    ├── test_transactions.py   # Transaction tests
    ├── test_budgets.py        # Budget tests
    └── test_cost_splitting.py # Cost splitting logic tests
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

![Database ERD](docs/images/database-erd.png)

_Complete ERD showing all tables, fields (with data types and nullable indicators), primary/foreign keys, and relationship cardinalities (1:M, M:M)_

**Text-based ERD (simplified overview):**

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

### Key Database Notes

**6 Core Tables:** User, Category, Member, Transaction, MembersTransaction (junction), Budget

**Key Relationships:**

- User owns Members, Transactions, Budgets, Categories (CASCADE DELETE)
- Transaction links to Category (SET NULL on delete), User, and Members via junction table
- Budget can belong to User OR Member (XOR validation), optionally filtered by Category

**Important Implementation Details:**

- **Members:** Data entities managed by user, NOT separate user accounts
- **Cost Splitting:** Transaction has `user_participates` flag to control split logic
- **Budget Types:** 4 combinations (User/Member × Total/Category)
- **Budget XOR Constraint:** Budget must have EITHER `user_id` OR `member_id` (not both, not neither). There is NO separate Members_Budget junction table - the Budget table directly connects to both User and Member via optional foreign keys.
- **MembersTransaction:** Pure junction table implementing many-to-many relationship between Transaction and Member for cost splitting
- **System Categories:** Auto-seeded on first run (Transport, Utilities, Entertainment, Food, Healthcare, Shopping, Other)
- **Constraints:** Bcrypt password hashing, composite PK on junction table, alert thresholds (0-100%)

---

## Features & Functionality

**For feature overview and descriptions**, see [README.md](README.md#features).

### Cost Splitting System

The application implements intelligent cost splitting with three modes:

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

**Example Scenarios:**

1. **Groceries (Shared)** - £100, Sarah (Spouse), User Participates: Yes → User pays £50, Sarah owes £50
2. **Kids' School Trip (Members-Only)** - £60, Emma & Jack (Children), User Participates: No → User pays £60 upfront, Emma owes £30, Jack owes £30
3. **Personal Coffee** - £5, No Members → User pays £5, no splitting

### Technical Implementation

- **Authentication:** Flask-Login 0.7.0 with bcrypt password hashing, `@login_required` decorator
- **Data Export:** ReportLab 4.4.4 for PDF generation, CSV with filtered results
- **Budget Types:** User/Member × Total/Category (4 combinations), XOR validation
- **Admin Interface:** Flask-Admin with role-based access control (`is_admin` flag)

---

## Technology Stack

**Backend**: Flask 3.1.2, Python 3.13, SQLAlchemy 2.0.36, Flask-Login, Flask-WTF, ReportLab (PDF)  
**Database**: SQLite (dev) / PostgreSQL (production) with Flask-Migrate  
**Frontend**: HTML5, CSS3, Vanilla JavaScript  
**Testing**: pytest 8.4.2 (49 tests, 100% passing)

**For complete dependency list and versions**, see [README.md](README.md#technology-stack) and `requirements.txt`.

---

## Installation & Setup

**For installation instructions**, see [README.md](README.md#installation).

---

## User Guide

**For feature usage instructions**, see the application's built-in FAQ page (`/faq` route).

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

**Test Suite**: 49 tests (100% passing) | **Framework**: pytest 8.4.2

**For test strategy and methodology**, see [README.md](README.md#testing).

### Test Structure

- `test_auth.py` - Authentication (15 tests)
- `test_transactions.py` - Transaction CRUD (6 tests)
- `test_family_management.py` - Family members (8 tests)
- `test_budgets.py` - Budget management (10 tests)
- `test_cost_splitting.py` - Cost splitting logic (10 tests)

### Key Fixtures (`conftest.py`)

- `app()` - Test Flask app with in-memory SQLite
- `client(app)` - Flask test client
- `test_user(app)` - Standard test user
- `admin_user(app)` - Admin test user
- `auth_client()` - Authenticated test client
- `test_member()` - Test family member

### Coverage Areas

- User registration/login/logout
- Transaction CRUD operations
- Family member management
- Cost splitting calculations (personal/shared/members-only)
- Budget alerts and thresholds
- Admin access control
- Data validation and error handling

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

---

## Future Enhancements

**For planned features and roadmap**, see [README.md](README.md#future-enhancements).

Key priorities: Enhanced analytics, notifications system, receipt scanning, mobile app, banking integration, machine learning features.

---

## Project Achievements

**100% Test Coverage** with 49/49 tests passing  
**Secure Authentication** with bcrypt password hashing  
**Intelligent Cost Splitting** with flexible participation logic  
**Real-Time Budget Alerts** with customizable thresholds  
**Data Export** in CSV and PDF formats  
**Responsive Design** for desktop and mobile  
**Production Deployment** on PythonAnywhere

---

## Deployment

**Status:** Deployed  
**Platform:** PythonAnywhere  
**URL:** [Smart Expenses Tracker](#) _(Live Demo)_  
**Database:** PostgreSQL (production)  
**Environment:** Production

### Deployment Configuration

- **Security:** SSL/HTTPS enabled, secure session cookies
- **Database:** PostgreSQL with automated daily backups
- **Email:** SMTP server configured for budget alerts and notifications
- **Error Logging:** Sentry integration for production monitoring
- **Performance:** Optimized static file serving, database connection pooling
- **Environment Variables:** Production secrets configured via platform settings

---

## Support & Contact

- **Repository:** https://github.com/FlaviaMorgulis/Smart_Expenses_Tracker
- **Issues:** Submit via GitHub Issues
- **Developers:** [Flavia Morgulis](https://github.com/FlaviaMorgulis) | [Behram Aras](https://github.com/behramaras)

---

**Document Version:** 1.0  
**Last Updated:** November 2025
