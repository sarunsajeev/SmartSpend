# SmartSpend – Personal Finance Tracker

SmartSpend is a Django internship project for recording income and expenses, tracking savings goals and subscriptions, reviewing financial activity, and downloading private PDF statements. Django is the core framework: it owns authentication, database models, form validation, URL routing, views, templates, migrations, and the admin site.

## Features

- Django registration, login, logout, profile editing, and password changes.
- User-owned income, expense, and investment transactions with category validation.
- Private transaction history with search, type/category/date filters, sorting, pagination, and details.
- Custom income and expense categories, plus starter categories for each new account.
- Savings goals and recurring subscriptions with create, edit, and delete forms.
- Dashboard and analytics charts calculated from the signed-in user's database records.
- Monthly, yearly, custom-range, income, expense, and complete-history PDF statements.
- Django Admin management for users, transactions, categories, goals, and subscriptions.
- Responsive SmartSpend layouts using custom CSS, Bootstrap components, and Chart.js.

## Technologies

- Python 3.14 (the project also works with supported Python versions for the pinned packages)
- Django 5.2.19
- SQLite
- ReportLab 5.1.0 for PDF statements
- HTML, custom CSS, JavaScript, Bootstrap, and Chart.js
- `python-dotenv` for local environment settings

## Install and run on Windows

Open PowerShell in the SmartSpend project folder. The commands below use the project's virtual-environment Python directly.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create `.env` from the example only if you do not already have a local `.env` file:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Set `DJANGO_SECRET_KEY` in `.env` to a private random value. Keep `.env` on your computer and do not commit it. For local development use `DJANGO_DEBUG=True` and `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost`.

Apply database migrations and start the development server:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open <http://127.0.0.1:8000/> and register an account. For a staff account that can use Django Admin, create a superuser in another PowerShell window:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Then open <http://127.0.0.1:8000/admin/>. Django Admin requires an authenticated staff account and the relevant model permissions. The custom account model is `accounts.User`; Django stores password hashes, never plain-text passwords.

For deployment, set `DJANGO_DEBUG=False`, provide a production secret and host list, and serve the site over HTTPS. HTTPS-only cookies and HSTS are enabled when debug mode is off.

## PDF statements

Sign in and open **Statements** in the sidebar. Choose all transactions, income, or expenses, then select one month, one year, a custom date range, or complete history. The PDF is generated on demand and returned as a private download; SmartSpend does not save a second copy of the statement. Totals, expense categories, chart bars, transactions, subscriptions, and goals are queried for the current user. Amounts in the statement are labeled in INR.

The report's budget section summarizes the existing savings-goal model. The project does not currently have a separate category spending-limit model.

## Database

The local database is `db.sqlite3` in the project root. Django ORM queries and migrations manage the data. The data migration `transactions.0003_seed_default_categories` adds starter categories for existing accounts; registration adds them for new accounts. PDF reports are generated in memory and do not change the database schema.

## Project structure

```text
config/                 Django settings and root URL routing
accounts/               Custom user, authentication, profile, account admin
transactions/           Transaction/category models, forms, views, admin
budgets/                Savings-goal model, forms, views, admin
subscriptions/           Recurring-payment model, forms, views, admin
dashboard/              Database-backed dashboard and analytics
reports/                Statement options, user-scoped report queries, PDF generation
templates/               Shared layout and Django page templates
static/                  Custom CSS and JavaScript
manage.py                Django command-line entry point
requirements.txt         Python package versions
```

Useful maintenance commands:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```
