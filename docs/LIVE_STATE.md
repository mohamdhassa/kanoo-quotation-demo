# Current V1 Live State

Snapshot date: 2026-08-24.

## Repository
`mohamdhassa/kanoo-quotation-demo`

## Current User Seeding
The current V1 code no longer automatically generates 15 advisor accounts. The initial-user seed ensures the configured manager exists; dropdown defaults are seeded separately.

## Supabase Application Tables
- users
- quotations
- status_history
- audit_logs
- dropdown_options

## Point-in-Time Counts Observed During Documentation Review
- users: 5
- quotations: 19
- status_history: 5
- audit_logs: 85
- dropdown_options: 46

These counts are a snapshot and will change with normal use.

## Roles
- manager
- advisor

## Render Configuration
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Health: `/health`

## Note
The live database is authoritative for current operational record counts.