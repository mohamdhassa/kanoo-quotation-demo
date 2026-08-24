# Database Documentation

## Production
V1 uses PostgreSQL hosted by Supabase. If `DATABASE_URL` is omitted locally, the application uses SQLite.

## Tables

### users
`id`, `username`, `password_hash`, `full_name`, `role`, `active`

### quotations
`id`, `customer_name`, `vehicle_type`, `vrn`, `damage_area`, `service_offered`, `number_of_panels`, `price_quoted`, `approved`, `reason_for_refusal`, `advisor_id`, `created_at`, `updated_at`

### status_history
`id`, `quotation_id`, `old_status`, `new_status`, `changed_by`, `changed_at`

Used to retain quotation status history and identify recovered Rejected -> Approved sales.

### audit_logs
`id`, `user_id`, `username`, `full_name`, `action`, `entity_type`, `entity_id`, `details`, `created_at`

### dropdown_options
`id`, `category`, `value`, `sort_order`, `active`

Categories: `vehicle`, `damage_area`, `service`, `refusal_reason`.

## Relationships
- `quotations.advisor_id -> users.id`
- `status_history.quotation_id -> quotations.id`
- `status_history.changed_by -> users.id`
- `audit_logs.user_id -> users.id`

## Current Supabase Structure
Application tables: `users`, `quotations`, `status_history`, `audit_logs`, `dropdown_options`.

RLS is currently enabled on the application tables. Flask remains the primary application authorization boundary because the server connects directly to PostgreSQL.

## Data Rules
- A quotation must reference a valid advisor.
- Historical dropdown text remains on existing quotations if an option is disabled.
- Disable advisors with history rather than deleting them.

## Backup
Create a database backup before schema changes, major releases or data repairs.

## Future Recommendation
Introduce Alembic/Flask-Migrate for version-controlled schema migrations.