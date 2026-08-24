# Security Notes

## Existing Controls
- Werkzeug password hashing
- active/disabled accounts
- server-side login and role checks
- HTTP-only session cookie
- SameSite=Lax
- secure production cookie configuration
- environment-based secrets
- audit logging
- server-side field validation

## Never Commit
- Supabase database password
- live `DATABASE_URL`
- Flask `SECRET_KEY`
- live user passwords
- customer-data exports

## Account Handling
Disable access immediately when no longer required. Keep user rows that own quotation history.

## Production Hardening Recommendations
1. Corporate SSO / identity integration
2. CSRF protection
3. Login rate limiting
4. Password policy and temporary-password reset
5. Alembic migrations
6. Automated backups and restore testing
7. Separate development/staging/production environments
8. Centralized application/error logging
9. Dependency/security scanning
10. ICT infrastructure/security review
11. Least-privilege database credentials
12. Customer-data retention policy

Customer records, screenshots, exports and backups must be treated as company data.