# Cash Quotation System

A complete Flask application for body-shop cash quotations.

## Included

- Login with Advisor and Manager roles
- Responsive advisor data-entry page
- Search quotations by full or partial VRN
- Change a rejected quotation to approved
- Automatic date, time and advisor recording
- SQLite database created automatically
- Status-change history stored in the database
- Manager dashboard with filters, KPIs, charts and records table

## Run on Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The root page automatically opens Login.

## Demo accounts

- Advisor: `advisor` / `advisor123`
- Manager: `manager` / `manager123`

## Database

The application creates `instance/quotation_system.db` automatically on first run.

Before deployment, set a strong `SECRET_KEY` environment variable and change the demo passwords.

## Multiple users

The system supports any number of Advisor and Manager accounts. Each quotation stores the ID of the advisor who was logged in when it was created, so the Manager dashboard can analyze results separately by advisor.

Create a user interactively:

```bash
python manage_users.py add
```

Example without prompts:

```bash
python manage_users.py add --username ahmed --name "Ahmed Ali" --role advisor --password ChangeMe123
```

List all users:

```bash
python manage_users.py list
```

Reset a password:

```bash
python manage_users.py reset-password ahmed
```

Disable or re-enable a user without deleting their quotation history:

```bash
python manage_users.py disable ahmed
python manage_users.py enable ahmed
```

Do not delete old advisor rows from the database because quotations refer to those users for historical reporting. Disable the login instead.

## Initial multi-user accounts
The app automatically seeds 15 advisor accounts (`advisor01` through `advisor15`) plus the manager account on first run. See `ADVISOR_ACCOUNTS.txt` for the development credentials. Change all starter passwords before production use.

## Manager dashboard
The manager dashboard supports filtering by date, advisor name, vehicle, status, damage area and service. Analytics include approval rate, quoted/approved/rejected value, recovered sales, advisor performance, advisor approval rates, advisor values, vehicle/service/damage/refusal distributions, monthly trend, hourly activity and day-of-week activity.

## Excel export
The **Export Excel** button downloads the exact records matching the current dashboard filters. The workbook contains the quotation number, date/time, advisor, customer, vehicle, VRN, damage area, service, panels, price, status, refusal reason and last updated time.

## Daily Advisor Performance
The manager dashboard includes a date-based Daily Advisor Performance report. Every advisor account is included in the report even when the advisor has zero quotations or zero approved sales for that day. The report includes offers, approved sales, rejected offers, approval rate, quoted/approved values, panels, and recovered rejected-to-approved sales. The selected day can be exported to a branded Excel workbook from the dashboard.

## Branding
The supplied Ebrahim K. Kanoo full logo and mark are stored in `static/images/` and used on login, page headers, the favicon, and the daily Excel report.
