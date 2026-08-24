# V1 Project Handover

## Repository
`mohamdhassa/kanoo-quotation-demo`

## Purpose
Centralize Body & Paint quotation entry, follow-up and management analysis while retaining Excel reporting.

## Roles
- Advisor
- Manager

## Technology
Python, Flask, SQLAlchemy, Supabase PostgreSQL, SQLite fallback, HTML, CSS, JavaScript, Chart.js, XlsxWriter, Gunicorn and Render.

## Important Files
- `app.py`
- `requirements.txt`
- `render.yaml`
- `.env.example`
- `templates/`
- `static/`

## Database
- users
- quotations
- status_history
- audit_logs
- dropdown_options

## Before Editing Production
1. Read architecture/database documentation.
2. Back up the database if data/schema can be affected.
3. Work on a test copy first.
4. Never commit secrets.
5. Test both roles.
6. Test dashboard, search/edit and Excel exports.

## V1 Boundary
V1 is the current single-operation, two-role production system. Multi-branch functionality is being developed independently as V2.

## Handover Principle
If formally adopted, production infrastructure, secrets, backups and deployment permissions should move through approved company/ICT-controlled accounts rather than informal sharing of personal credentials.