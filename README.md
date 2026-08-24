# Cash Quotation System — V1

A Flask-based Body & Paint quotation management system with advisor quotation entry/search and a management analytics dashboard.

## Main Features

### Advisor
- Login
- New quotation entry
- Automatic quotation number, date/time and advisor
- Approved or Rejected status
- Reason for refusal
- Full/partial VRN search
- Edit previous quotation
- Rejected -> Approved recovery tracking

### Manager
- Dashboard filters and KPIs
- Advisor performance analysis
- Recovered-sales analysis
- Vehicle/service/damage/refusal analysis
- Daily, monthly, hourly and weekday charts
- Daily advisor performance
- Filtered Excel export
- Daily-report Excel export
- User management
- Dropdown-list management
- Audit log

## Roles
V1 has two roles: `advisor` and `manager`.

The current V1 code does **not** automatically create 15 starter advisor accounts. Real advisor accounts are managed through the Manager user-management functions.

## Local Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. When `DATABASE_URL` is not configured, the application uses local SQLite.

## Production
The current production architecture is Render + Supabase PostgreSQL. Important environment variables are documented in `.env.example`.

## Documentation
Full V1 documentation is in [`docs/`](docs/INDEX.md):
- Architecture
- ERD
- Authentication and roles
- Database structure
- Routes and features
- Deployment
- Security
- Operations and maintenance
- Project handover
- Live-state snapshot

## Production Safety
Do not commit production secrets, customer-data exports, database passwords or live credentials to GitHub.

For users with quotation history, disable the account instead of deleting it so historical reporting remains correct.

## V2
Multi-branch functionality is being developed separately as V2 so the current V1 production system can remain stable until the new version is tested and approved.