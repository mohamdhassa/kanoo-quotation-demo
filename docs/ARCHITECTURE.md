# V1 System Architecture

## Purpose
V1 is a Flask web application for Body & Paint quotation recording, follow-up and management analysis.

## Production Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python Flask
- ORM: Flask-SQLAlchemy / SQLAlchemy
- Production database: Supabase PostgreSQL
- Local fallback: SQLite
- Hosting: Render
- Process: Gunicorn
- Charts: Chart.js
- Excel: XlsxWriter
- Timezone: Asia/Bahrain

## Architecture
```text
Browser
  -> HTTPS
Render
  -> Gunicorn / Flask
Application
  -> Authentication and sessions
  -> Advisor quotation workflow
  -> Manager dashboard
  -> User administration
  -> Dropdown administration
  -> Audit logging
  -> Excel exports
  -> SQLAlchemy
Supabase PostgreSQL
  -> users
  -> quotations
  -> status_history
  -> audit_logs
  -> dropdown_options
```

## Startup
The application creates missing tables, ensures the configured initial manager exists, and seeds missing dropdown defaults. The old automatic 15-advisor seed has been removed from the current V1 code.

## Environment
`DATABASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_FULL_NAME`, `APP_TIMEZONE`, `FLASK_DEBUG`.