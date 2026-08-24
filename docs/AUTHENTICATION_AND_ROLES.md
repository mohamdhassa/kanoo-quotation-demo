# Authentication and Roles

## Authentication
V1 uses application-managed username/password authentication. Passwords are stored using Werkzeug password hashes and are not stored as plain text.

## Session
After successful login the Flask session contains `user_id`, `username`, `full_name`, and `role`.

## Advisor
- Create quotations
- Search quotations by VRN
- Edit quotation status and refusal reason
- Support Rejected -> Approved recovery workflow

## Manager
- Full management dashboard
- Filters, KPIs and analytics
- Daily advisor performance
- Excel exports
- User management
- Password reset
- Enable/disable users
- Dropdown-list management
- Audit log

## Authorization
Protected pages use login and role checks on the server. UI visibility alone is never treated as authorization.

## Account Lifecycle
Create -> Active -> Disable -> Enable.

Accounts with quotation history should normally be disabled instead of deleted.

## Session Security
- HTTP-only cookie
- SameSite=Lax
- secure cookie in hosted production environments
- environment-based Flask `SECRET_KEY`

## Future Enterprise Recommendation
ICT should consider corporate SSO/identity integration for formal company-wide production use.