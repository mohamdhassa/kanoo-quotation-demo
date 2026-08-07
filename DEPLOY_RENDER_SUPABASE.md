# Demo Deployment: GitHub + Supabase + Render

## Architecture
- GitHub: source repository
- Render: Flask/Gunicorn web service
- Supabase: PostgreSQL database

## Supabase
The demo schema is already created in the connected Supabase project.
For Render, use Supabase Dashboard -> Connect -> Session pooler.
Copy the session-pooler PostgreSQL URI and replace the password placeholder with your database password.
Do not commit this URI to GitHub.

## Render
Create a Web Service from the GitHub repository.

- Runtime: Python 3
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Health check: `/health`

Environment variables:
- `DATABASE_URL`: Supabase Session pooler URI
- `SECRET_KEY`: long random value
- `ADMIN_USERNAME`: manager
- `ADMIN_PASSWORD`: strong demo manager password
- `ADMIN_FULL_NAME`: Body Shop Manager
- `APP_TIMEZONE`: Asia/Bahrain

After deployment visit `/health`. Expected response:
`{"status":"ok","database":"connected"}`

The first successful app start seeds the manager and starter advisor accounts if they do not exist.
Use Manager -> Users to replace starter accounts with real advisor names and passwords.
