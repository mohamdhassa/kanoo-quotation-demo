# Operations and Maintenance

## User Administration
Create users from Manager -> Users. If a user owns quotation history, disable the account rather than deleting it.

## Dropdown Administration
Manage vehicle, damage area, service and refusal-reason options from Manager -> Lists. Disable obsolete options to preserve historical data.

## Recommended Change Workflow
```text
Pull latest
-> feature/test copy
-> make change
-> test locally
-> test Advisor + Manager
-> backup DB if affected
-> commit/push
-> deploy
-> production smoke test
```

## Backups
Recommended: daily database backup, extra backup before schema changes or major releases, and periodic restore tests.

## Troubleshooting
### SQLite unable to open database file
Ensure `instance/` exists and is writable.

### Supabase password authentication failed
Verify pooler username, database password, host and port.

### invalid connection option pgbouncer
Remove unsupported `?pgbouncer=true` from the psycopg2 URL.

### Chart missing
Check Chart.js loading, canvas IDs, dashboard data, browser console and cache.

### Internal Server Error after template change
Check Render logs. Python datetime values should be formatted with Jinja `strftime()` rather than string slicing.

## Monitoring
Monitor Render service status, `/health`, deployment logs, database availability, audit-log growth and database storage.