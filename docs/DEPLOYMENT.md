# Deployment — Render + Supabase

## Topology
GitHub -> Render web service -> Supabase PostgreSQL

## Render
Build command:
`pip install -r requirements.txt`

Start command:
`gunicorn app:app`

Health check:
`/health`

## Environment Variables
- `SECRET_KEY`
- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_FULL_NAME`
- `APP_TIMEZONE`

Never commit production secrets.

## Supabase
Use the PostgreSQL session-pooler connection string compatible with psycopg2, normally port 5432.

Expected form:
`postgresql://postgres.<PROJECT_REF>:<PASSWORD>@<POOLER_HOST>:5432/postgres`

Do not append unsupported client options such as `?pgbouncer=true` to a psycopg2 DSN unless the application explicitly handles them.

## Deployment Smoke Test
1. Login
2. Advisor new quotation
3. VRN search
4. Edit quotation
5. Manager dashboard
6. Charts
7. User management
8. Dropdown lists
9. Excel exports
10. Audit log
11. Logout

## Rollback
Use the last known-good Render deployment/commit. If a release changed the schema, restore a compatible database backup as required.