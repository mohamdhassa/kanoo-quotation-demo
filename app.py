from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from functools import wraps
from io import BytesIO
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

import xlsxwriter
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, func, or_
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
COMPANY_LOGO_PATH = BASE_DIR / "static" / "images" / "ekk_full_logo.png"
APP_TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Bahrain"))


def local_now() -> datetime:
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def normalize_database_url(url: str) -> str:
    # Some cloud providers still expose the older postgres:// scheme.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'quotation_system.db'}")
)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "change-this-secret-key-before-deployment"),
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True


db = SQLAlchemy(app)

DEFAULT_VEHICLES = ["Corolla", "Camry", "Yaris", "Hilux", "Land Cruiser", "Prado", "Fortuner", "RAV4", "Highlander", "Rush", "Coaster", "Hiace", "Other"]
DEFAULT_DAMAGE_AREAS = ["Front Bumper", "Rear Bumper", "Front Fender LH", "Front Fender RH", "Front Door LH", "Front Door RH", "Rear Door LH", "Rear Door RH", "Quarter Panel LH", "Quarter Panel RH", "Bonnet", "Roof", "Tailgate", "Boot Lid", "Mirror", "Other"]
DEFAULT_SERVICES = ["Paint", "Repair", "Replace", "Polish", "Dent Removal", "Scratch Repair", "Smart Repair", "Bumper Repair", "Body Repair", "Other"]
DEFAULT_REFUSAL_REASONS = ["Price Too High", "Customer Not Interested", "Will Return Later", "Needs Approval", "No Time", "Already Repaired Elsewhere", "Insurance Related", "Other"]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    quotations = db.relationship("Quotation", back_populates="advisor", lazy="dynamic")


class Quotation(db.Model):
    __tablename__ = "quotations"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    vehicle_type = db.Column(db.String(80), nullable=False)
    vrn = db.Column(db.String(40), nullable=False, index=True)
    damage_area = db.Column(db.String(120), nullable=False)
    service_offered = db.Column(db.String(120), nullable=False)
    number_of_panels = db.Column(db.Integer, nullable=False)
    price_quoted = db.Column(db.Float, nullable=False)
    approved = db.Column(db.String(20), nullable=False)
    reason_for_refusal = db.Column(db.String(180))
    advisor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=local_now, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=local_now, onupdate=local_now)

    advisor = db.relationship("User", back_populates="quotations")
    history = db.relationship("StatusHistory", back_populates="quotation", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_quotations_created_advisor", "created_at", "advisor_id"),
    )


class StatusHistory(db.Model):
    __tablename__ = "status_history"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=local_now, index=True)

    quotation = db.relationship("Quotation", back_populates="history")



class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = db.Column(db.String(80), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    action = db.Column(db.String(80), nullable=False, index=True)
    entity_type = db.Column(db.String(40))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=local_now, index=True)


class DropdownOption(db.Model):
    __tablename__ = "dropdown_options"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False, index=True)
    value = db.Column(db.String(150), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (db.UniqueConstraint("category", "value", name="uq_dropdown_category_value"),)


DROPDOWN_DEFAULTS = {
    "vehicle": DEFAULT_VEHICLES,
    "damage_area": DEFAULT_DAMAGE_AREAS,
    "service": DEFAULT_SERVICES,
    "refusal_reason": DEFAULT_REFUSAL_REASONS,
}


def get_options(category: str, include_inactive: bool = False) -> list[str]:
    query = DropdownOption.query.filter_by(category=category)
    if not include_inactive:
        query = query.filter_by(active=True)
    rows = query.order_by(DropdownOption.sort_order.asc(), DropdownOption.value.asc()).all()
    if rows:
        return [row.value for row in rows]
    return list(DROPDOWN_DEFAULTS.get(category, []))


def seed_dropdown_options() -> None:
    for category, values in DROPDOWN_DEFAULTS.items():
        for order, value in enumerate(values, start=1):
            exists = DropdownOption.query.filter_by(category=category, value=value).first()
            if not exists:
                db.session.add(DropdownOption(category=category, value=value, sort_order=order, active=True))
    db.session.commit()


def write_audit(action: str, entity_type: str | None = None, entity_id: int | None = None, details: str | None = None, user: User | None = None) -> None:
    if user is None and session.get("user_id"):
        user = db.session.get(User, session.get("user_id"))
    username = user.username if user else session.get("username", "system")
    full_name = user.full_name if user else session.get("full_name", "System")
    db.session.add(AuditLog(
        user_id=user.id if user else None,
        username=username or "system",
        full_name=full_name or "System",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=(details or "")[:500] or None,
        created_at=local_now(),
    ))


def seed_initial_users() -> None:
    manager_username = os.getenv("ADMIN_USERNAME", "manager").strip().lower()
    manager_password = os.getenv("ADMIN_PASSWORD", "manager123")
    manager_name = os.getenv("ADMIN_FULL_NAME", "Manager")

    if not User.query.filter_by(username=manager_username).first():
        db.session.add(
            User(
                username=manager_username,
                password_hash=generate_password_hash(manager_password),
                full_name=manager_name,
                role="manager",
                active=True,
            )
        )

    # Keep the existing 15 starter advisor accounts so the current workflow
    # continues to work after deployment. Change their passwords before public use.
    for i in range(1, 16):
        username = f"advisor{i:02d}"
        if not User.query.filter_by(username=username).first():
            db.session.add(
                User(
                    username=username,
                    password_hash=generate_password_hash(f"Adv{i:02d}@2026"),
                    full_name=f"Advisor {i:02d}",
                    role="advisor",
                    active=True,
                )
            )
    db.session.commit()


def init_db() -> None:
    db.create_all()
    seed_initial_users()
    seed_dropdown_options()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                flash("You do not have permission to open that page.", "danger")
                return redirect(url_for("advisor_new" if session.get("role") == "advisor" else "manager_dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


@app.context_processor
def inject_lists():
    return dict(
        vehicles=get_options("vehicle"),
        damage_areas=get_options("damage_area"),
        services=get_options("service"),
        refusal_reasons=get_options("refusal_reason"),
    )


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("advisor_new" if session.get("role") == "advisor" else "manager_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username, active=True).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html")
        session.clear()
        session.update(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
        )
        write_audit("login", "user", user.id, "User signed in", user=user)
        db.session.commit()
        return redirect(url_for("advisor_new" if user.role == "advisor" else "manager_dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    if session.get("user_id"):
        write_audit("logout", "user", session.get("user_id"), "User signed out")
        db.session.commit()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/advisor/new", methods=["GET", "POST"])
@role_required("advisor")
def advisor_new():
    if request.method == "POST":
        data = {
            key: request.form.get(key, "").strip()
            for key in [
                "customer_name",
                "vehicle_type",
                "vrn",
                "damage_area",
                "service_offered",
                "number_of_panels",
                "price_quoted",
                "approved",
                "reason_for_refusal",
            ]
        }
        required = [
            "customer_name",
            "vehicle_type",
            "vrn",
            "damage_area",
            "service_offered",
            "number_of_panels",
            "price_quoted",
            "approved",
        ]
        if any(not data[key] for key in required):
            flash("Please complete all required fields.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())

        try:
            panels = int(data["number_of_panels"])
            price = float(data["price_quoted"])
            if panels < 1 or price < 0:
                raise ValueError
        except ValueError:
            flash("Panels and price must be valid positive numbers.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())

        if data["vehicle_type"] not in get_options("vehicle"):
            flash("Select a valid vehicle type.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())
        if data["damage_area"] not in get_options("damage_area"):
            flash("Select a valid damage area.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())
        if data["service_offered"] not in get_options("service"):
            flash("Select a valid service offered.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())
        if data["approved"] not in {"Rejected", "Approved"}:
            flash("Select a valid approval status.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())
        if data["approved"] == "Rejected" and not data["reason_for_refusal"]:
            flash("Select a reason for refusal.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())
        if data["approved"] == "Rejected" and data["reason_for_refusal"] not in get_options("refusal_reason"):
            flash("Select a valid reason for refusal.", "danger")
            return render_template("advisor/new_entry.html", form=data, now=local_now())
        if data["approved"] == "Approved":
            data["reason_for_refusal"] = ""

        now = local_now()
        quotation = Quotation(
            customer_name=data["customer_name"],
            vehicle_type=data["vehicle_type"],
            vrn=data["vrn"].upper(),
            damage_area=data["damage_area"],
            service_offered=data["service_offered"],
            number_of_panels=panels,
            price_quoted=price,
            approved=data["approved"],
            reason_for_refusal=data["reason_for_refusal"] or None,
            advisor_id=session["user_id"],
            created_at=now,
            updated_at=now,
        )
        db.session.add(quotation)
        db.session.flush()
        db.session.add(
            StatusHistory(
                quotation_id=quotation.id,
                old_status=None,
                new_status=data["approved"],
                changed_by=session["user_id"],
                changed_at=now,
            )
        )
        write_audit("quotation_created", "quotation", quotation.id, f"VRN {quotation.vrn}; status {quotation.approved}; BHD {quotation.price_quoted:.3f}")
        db.session.commit()
        flash(f"Quotation No. {quotation.id} saved successfully.", "success")
        return redirect(url_for("advisor_new"))

    return render_template("advisor/new_entry.html", form={}, now=local_now())


@app.route("/advisor/search")
@role_required("advisor")
def advisor_search():
    vrn = request.args.get("vrn", "").strip().upper()
    rows = []
    if vrn:
        rows = (
            Quotation.query
            .join(User, User.id == Quotation.advisor_id)
            .filter(Quotation.vrn.ilike(f"%{vrn}%"))
            .order_by(Quotation.created_at.desc())
            .all()
        )
    return render_template("advisor/search.html", quotations=rows, vrn=vrn)


@app.route("/advisor/quotation/<int:quotation_id>/edit", methods=["GET", "POST"])
@role_required("advisor")
def edit_quotation(quotation_id: int):
    quotation = db.session.get(Quotation, quotation_id)
    if not quotation:
        flash("Quotation not found.", "danger")
        return redirect(url_for("advisor_search"))

    if request.method == "POST":
        approved = request.form.get("approved", "").strip()
        reason = request.form.get("reason_for_refusal", "").strip()
        if approved not in {"Rejected", "Approved"}:
            flash("Select a valid status.", "danger")
            return render_template("advisor/edit.html", quotation=quotation)
        if approved == "Rejected" and not reason:
            flash("Select a reason for refusal.", "danger")
            return render_template("advisor/edit.html", quotation=quotation)
        if approved == "Rejected" and reason not in get_options("refusal_reason"):
            flash("Select a valid reason for refusal.", "danger")
            return render_template("advisor/edit.html", quotation=quotation)
        if approved == "Approved":
            reason = ""

        old_status = quotation.approved
        now = local_now()
        quotation.approved = approved
        quotation.reason_for_refusal = reason or None
        quotation.updated_at = now
        if old_status != approved:
            db.session.add(
                StatusHistory(
                    quotation_id=quotation.id,
                    old_status=old_status,
                    new_status=approved,
                    changed_by=session["user_id"],
                    changed_at=now,
                )
            )
        write_audit("quotation_updated", "quotation", quotation.id, f"VRN {quotation.vrn}; {old_status} → {approved}")
        db.session.commit()
        flash("Quotation updated successfully.", "success")
        return redirect(url_for("advisor_search", vrn=quotation.vrn))

    return render_template("advisor/edit.html", quotation=quotation)


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def filtered_quotation_query():
    query = Quotation.query.join(User, User.id == Quotation.advisor_id)

    advisor = request.args.get("advisor", "").strip()
    vehicle_type = request.args.get("vehicle_type", "").strip()
    damage_area = request.args.get("damage_area", "").strip()
    service_offered = request.args.get("service_offered", "").strip()
    approved = request.args.get("approved", "").strip()
    date_from = parse_date(request.args.get("date_from", "").strip())
    date_to = parse_date(request.args.get("date_to", "").strip())

    if advisor.isdigit():
        query = query.filter(Quotation.advisor_id == int(advisor))
    if vehicle_type:
        query = query.filter(Quotation.vehicle_type == vehicle_type)
    if damage_area:
        query = query.filter(Quotation.damage_area == damage_area)
    if service_offered:
        query = query.filter(Quotation.service_offered == service_offered)
    if approved:
        query = query.filter(Quotation.approved == approved)
    if date_from:
        query = query.filter(Quotation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Quotation.created_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))

    return query


def group_counter(rows, attr: str):
    counter = Counter(getattr(row, attr) or "Not specified" for row in rows)
    return sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))


def build_dashboard(rows: list[Quotation]):
    total = len(rows)
    approved_rows = [q for q in rows if q.approved == "Approved"]
    rejected_rows = [q for q in rows if q.approved == "Rejected"]
    prices = [float(q.price_quoted or 0) for q in rows]
    panels = [int(q.number_of_panels or 0) for q in rows]

    summary = {
        "total": total,
        "approved": len(approved_rows),
        "rejected": len(rejected_rows),
        "total_value": sum(prices),
        "approved_value": sum(float(q.price_quoted or 0) for q in approved_rows),
        "rejected_value": sum(float(q.price_quoted or 0) for q in rejected_rows),
        "average_quote": mean(prices) if prices else 0,
        "average_panels": mean(panels) if panels else 0,
    }

    row_ids = {q.id for q in rows}
    recovery_events = (
        StatusHistory.query
        .filter(
            StatusHistory.quotation_id.in_(row_ids) if row_ids else False,
            StatusHistory.old_status == "Rejected",
            StatusHistory.new_status == "Approved",
        )
        .order_by(StatusHistory.changed_at.asc())
        .all()
        if row_ids
        else []
    )
    first_recovery = {}
    for event in recovery_events:
        first_recovery.setdefault(event.quotation_id, event)

    row_by_id = {q.id: q for q in rows}
    recovered_quotations = [row_by_id[qid] for qid in first_recovery if qid in row_by_id]
    recovery_hours = []
    for qid, event in first_recovery.items():
        quotation = row_by_id.get(qid)
        if quotation and quotation.created_at and event.changed_at:
            recovery_hours.append((event.changed_at - quotation.created_at).total_seconds() / 3600)

    recovered = {
        "recovered_count": len(recovered_quotations),
        "recovered_value": sum(float(q.price_quoted or 0) for q in recovered_quotations),
        "avg_recovery_hours": mean(recovery_hours) if recovery_hours else 0,
    }

    advisor_stats = defaultdict(lambda: {"total": 0, "approved": 0, "quoted_value": 0.0, "approved_value": 0.0})
    for q in rows:
        name = q.advisor.full_name if q.advisor else "Unknown"
        item = advisor_stats[name]
        item["total"] += 1
        item["quoted_value"] += float(q.price_quoted or 0)
        if q.approved == "Approved":
            item["approved"] += 1
            item["approved_value"] += float(q.price_quoted or 0)

    advisor_items = []
    for name, item in advisor_stats.items():
        advisor_items.append(
            {
                "label": name,
                **item,
                "approval_rate": round((item["approved"] / item["total"] * 100), 1) if item["total"] else 0,
            }
        )
    advisor_items.sort(key=lambda x: (-x["total"], x["label"]))

    vehicle_items = group_counter(rows, "vehicle_type")
    service_items = group_counter(rows, "service_offered")
    damage_items = group_counter(rows, "damage_area")
    refusal_counter = Counter((q.reason_for_refusal or "Not specified") for q in rejected_rows)
    refusal_items = sorted(refusal_counter.items(), key=lambda x: (-x[1], x[0]))

    by_month = Counter(q.created_at.strftime("%Y-%m") for q in rows)
    month_items = sorted(by_month.items())

    by_hour = Counter(q.created_at.strftime("%H") for q in rows)
    hour_items = sorted(by_hour.items())

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_weekday = Counter(q.created_at.strftime("%A") for q in rows)
    weekday_items = [(day, by_weekday[day]) for day in weekday_order if by_weekday[day]]

    daily = defaultdict(lambda: {"total": 0, "approved": 0, "rejected": 0})
    for q in rows:
        key = q.created_at.date()
        daily[key]["total"] += 1
        daily[key]["approved" if q.approved == "Approved" else "rejected"] += 1

    requested_from = parse_date(request.args.get("date_from", "").strip())
    requested_to = parse_date(request.args.get("date_to", "").strip())
    series_start = requested_from or (min(daily) if daily else None)
    series_end = requested_to or (max(daily) if daily else None)

    daily_labels, daily_totals, daily_approved, daily_rejected = [], [], [], []
    if series_start and series_end and series_end >= series_start:
        cursor = series_start
        while cursor <= series_end:
            values = daily[cursor]
            daily_labels.append(cursor.strftime("%d %b %Y"))
            daily_totals.append(values["total"])
            daily_approved.append(values["approved"])
            daily_rejected.append(values["rejected"])
            cursor += timedelta(days=1)

    chart_data = {
        "advisor_labels": [x["label"] for x in advisor_items],
        "advisor_totals": [x["total"] for x in advisor_items],
        "advisor_approved": [x["approved"] for x in advisor_items],
        "advisor_rates": [x["approval_rate"] for x in advisor_items],
        "advisor_quoted_values": [x["quoted_value"] for x in advisor_items],
        "advisor_approved_values": [x["approved_value"] for x in advisor_items],
        "vehicle_labels": [x[0] for x in vehicle_items],
        "vehicle_values": [x[1] for x in vehicle_items],
        "service_labels": [x[0] for x in service_items],
        "service_values": [x[1] for x in service_items],
        "damage_labels": [x[0] for x in damage_items],
        "damage_values": [x[1] for x in damage_items],
        "refusal_labels": [x[0] for x in refusal_items],
        "refusal_values": [x[1] for x in refusal_items],
        "month_labels": [x[0] for x in month_items],
        "month_values": [x[1] for x in month_items],
        "daily_labels": daily_labels,
        "daily_totals": daily_totals,
        "daily_approved": daily_approved,
        "daily_rejected": daily_rejected,
        "hour_labels": [f"{x[0]}:00" for x in hour_items],
        "hour_values": [x[1] for x in hour_items],
        "weekday_labels": [x[0] for x in weekday_items],
        "weekday_values": [x[1] for x in weekday_items],
    }
    return summary, recovered, chart_data



def build_daily_advisor_performance(report_date: date):
    """Return one performance row for every advisor, including zero-activity advisors."""
    advisors = User.query.filter_by(role="advisor").order_by(User.full_name.asc()).all()
    start = datetime.combine(report_date, datetime.min.time())
    end = start + timedelta(days=1)

    day_rows = (
        Quotation.query
        .filter(Quotation.created_at >= start, Quotation.created_at < end)
        .all()
    )
    by_advisor = defaultdict(list)
    for q in day_rows:
        by_advisor[q.advisor_id].append(q)

    # Recovered sale = a quotation that changed from Rejected to Approved on the report date.
    recovery_events = (
        StatusHistory.query
        .join(Quotation, Quotation.id == StatusHistory.quotation_id)
        .filter(
            StatusHistory.old_status == "Rejected",
            StatusHistory.new_status == "Approved",
            StatusHistory.changed_at >= start,
            StatusHistory.changed_at < end,
        )
        .all()
    )
    recovery_by_advisor = defaultdict(list)
    for event in recovery_events:
        if event.quotation:
            recovery_by_advisor[event.quotation.advisor_id].append(event.quotation)

    performance = []
    for advisor in advisors:
        rows = by_advisor.get(advisor.id, [])
        approved = [q for q in rows if q.approved == "Approved"]
        rejected = [q for q in rows if q.approved == "Rejected"]
        recovered = recovery_by_advisor.get(advisor.id, [])
        total = len(rows)
        total_value = sum(float(q.price_quoted or 0) for q in rows)
        approved_value = sum(float(q.price_quoted or 0) for q in approved)
        recovered_value = sum(float(q.price_quoted or 0) for q in recovered)
        total_panels = sum(int(q.number_of_panels or 0) for q in rows)
        performance.append({
            "advisor_id": advisor.id,
            "advisor_name": advisor.full_name,
            "username": advisor.username,
            "active": advisor.active,
            "total": total,
            "approved": len(approved),
            "rejected": len(rejected),
            "approval_rate": round((len(approved) / total * 100), 1) if total else 0.0,
            "quoted_value": total_value,
            "approved_value": approved_value,
            "average_quote": (total_value / total) if total else 0.0,
            "panels": total_panels,
            "recovered": len(recovered),
            "recovered_value": recovered_value,
        })

    totals = {
        "total": sum(x["total"] for x in performance),
        "approved": sum(x["approved"] for x in performance),
        "rejected": sum(x["rejected"] for x in performance),
        "quoted_value": sum(x["quoted_value"] for x in performance),
        "approved_value": sum(x["approved_value"] for x in performance),
        "panels": sum(x["panels"] for x in performance),
        "recovered": sum(x["recovered"] for x in performance),
        "recovered_value": sum(x["recovered_value"] for x in performance),
    }
    totals["approval_rate"] = round((totals["approved"] / totals["total"] * 100), 1) if totals["total"] else 0.0
    totals["average_quote"] = (totals["quoted_value"] / totals["total"]) if totals["total"] else 0.0
    return performance, totals


def get_daily_report_date() -> date:
    return parse_date(request.args.get("daily_date", "").strip()) or local_now().date()


@app.route("/manager/dashboard")
@role_required("manager")
def manager_dashboard():
    advisors = User.query.filter_by(role="advisor").order_by(User.full_name.asc()).all()
    rows = filtered_quotation_query().order_by(Quotation.created_at.desc()).all()
    summary, recovered, chart_data = build_dashboard(rows)
    approval_rate = round((summary["approved"] / summary["total"] * 100), 1) if summary["total"] else 0
    daily_report_date = get_daily_report_date()
    daily_performance, daily_totals = build_daily_advisor_performance(daily_report_date)
    activity_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(12).all()

    # The template expects a flattened advisor_name value for the table.
    recent = []
    for q in rows[:100]:
        recent.append(
            {
                "id": q.id,
                "created_at": q.created_at.isoformat(timespec="seconds"),
                "advisor_name": q.advisor.full_name if q.advisor else "Unknown",
                "customer_name": q.customer_name,
                "vehicle_type": q.vehicle_type,
                "vrn": q.vrn,
                "damage_area": q.damage_area,
                "service_offered": q.service_offered,
                "number_of_panels": q.number_of_panels,
                "price_quoted": q.price_quoted,
                "approved": q.approved,
                "reason_for_refusal": q.reason_for_refusal,
            }
        )

    return render_template(
        "manager/dashboard.html",
        summary=summary,
        recovered=recovered,
        approval_rate=approval_rate,
        advisors=advisors,
        recent=recent,
        chart_data=chart_data,
        daily_report_date=daily_report_date,
        daily_performance=daily_performance,
        daily_totals=daily_totals,
        activity_logs=activity_logs,
    )


@app.route("/manager/daily-report.xlsx")
@role_required("manager")
def manager_daily_report_excel():
    report_date = get_daily_report_date()
    performance, totals = build_daily_advisor_performance(report_date)

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    sheet = workbook.add_worksheet("Daily Advisor Performance")

    navy = "#00539B"
    dark_navy = "#17365D"
    light_blue = "#DDEBF7"
    light_gray = "#F2F2F2"
    green = "#E2F0D9"
    red = "#FCE4D6"

    title_fmt = workbook.add_format({"bold": True, "font_size": 18, "font_color": dark_navy, "valign": "vcenter"})
    subtitle_fmt = workbook.add_format({"font_size": 11, "font_color": "#666666"})
    header_fmt = workbook.add_format({"bold": True, "bg_color": navy, "font_color": "#FFFFFF", "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True})
    name_fmt = workbook.add_format({"border": 1, "valign": "vcenter"})
    inactive_fmt = workbook.add_format({"border": 1, "valign": "vcenter", "font_color": "#888888", "bg_color": light_gray})
    int_fmt = workbook.add_format({"border": 1, "align": "center", "num_format": "0"})
    pct_fmt = workbook.add_format({"border": 1, "align": "center", "num_format": "0.0%"})
    money_fmt = workbook.add_format({"border": 1, "num_format": '0.000 "BHD"'})
    total_label_fmt = workbook.add_format({"bold": True, "bg_color": light_blue, "border": 1})
    total_int_fmt = workbook.add_format({"bold": True, "bg_color": light_blue, "border": 1, "align": "center", "num_format": "0"})
    total_pct_fmt = workbook.add_format({"bold": True, "bg_color": light_blue, "border": 1, "align": "center", "num_format": "0.0%"})
    total_money_fmt = workbook.add_format({"bold": True, "bg_color": light_blue, "border": 1, "num_format": '0.000 "BHD"'})

    sheet.set_row(0, 58)
    if COMPANY_LOGO_PATH.exists():
        sheet.insert_image("A1", str(COMPANY_LOGO_PATH), {"x_scale": 0.25, "y_scale": 0.25, "x_offset": 4, "y_offset": 4})
    sheet.merge_range("D1:L1", "Body & Paint - Daily Advisor Performance", title_fmt)
    sheet.merge_range("D2:L2", f"Report date: {report_date.strftime('%d/%m/%Y')}  |  Generated: {local_now().strftime('%d/%m/%Y %H:%M')}", subtitle_fmt)

    headers = [
        "Advisor", "Account Status", "Offers Entered", "Approved Sales", "Rejected",
        "Approval Rate", "Quoted Value", "Approved Value", "Average Quote",
        "Panels", "Recovered Sales", "Recovered Value",
    ]
    header_row = 3
    for col, header in enumerate(headers):
        sheet.write(header_row, col, header, header_fmt)

    for idx, item in enumerate(performance, start=header_row + 1):
        row_fmt = name_fmt if item["active"] else inactive_fmt
        sheet.write(idx, 0, item["advisor_name"], row_fmt)
        sheet.write(idx, 1, "Active" if item["active"] else "Inactive", row_fmt)
        sheet.write_number(idx, 2, item["total"], int_fmt)
        sheet.write_number(idx, 3, item["approved"], int_fmt)
        sheet.write_number(idx, 4, item["rejected"], int_fmt)
        sheet.write_number(idx, 5, item["approval_rate"] / 100, pct_fmt)
        sheet.write_number(idx, 6, item["quoted_value"], money_fmt)
        sheet.write_number(idx, 7, item["approved_value"], money_fmt)
        sheet.write_number(idx, 8, item["average_quote"], money_fmt)
        sheet.write_number(idx, 9, item["panels"], int_fmt)
        sheet.write_number(idx, 10, item["recovered"], int_fmt)
        sheet.write_number(idx, 11, item["recovered_value"], money_fmt)

    total_row = header_row + 1 + len(performance)
    sheet.write(total_row, 0, "TEAM TOTAL", total_label_fmt)
    sheet.write(total_row, 1, "", total_label_fmt)
    sheet.write_number(total_row, 2, totals["total"], total_int_fmt)
    sheet.write_number(total_row, 3, totals["approved"], total_int_fmt)
    sheet.write_number(total_row, 4, totals["rejected"], total_int_fmt)
    sheet.write_number(total_row, 5, totals["approval_rate"] / 100, total_pct_fmt)
    sheet.write_number(total_row, 6, totals["quoted_value"], total_money_fmt)
    sheet.write_number(total_row, 7, totals["approved_value"], total_money_fmt)
    sheet.write_number(total_row, 8, totals["average_quote"], total_money_fmt)
    sheet.write_number(total_row, 9, totals["panels"], total_int_fmt)
    sheet.write_number(total_row, 10, totals["recovered"], total_int_fmt)
    sheet.write_number(total_row, 11, totals["recovered_value"], total_money_fmt)

    # Make zero-activity and sales performance easy to scan.
    first_data = header_row + 1
    last_data = max(first_data, total_row - 1)
    sheet.conditional_format(first_data, 2, last_data, 2, {"type": "cell", "criteria": "==", "value": 0, "format": workbook.add_format({"bg_color": light_gray, "font_color": "#777777"})})
    sheet.conditional_format(first_data, 3, last_data, 3, {"type": "cell", "criteria": ">", "value": 0, "format": workbook.add_format({"bg_color": green})})
    sheet.conditional_format(first_data, 4, last_data, 4, {"type": "cell", "criteria": ">", "value": 0, "format": workbook.add_format({"bg_color": red})})

    sheet.freeze_panes(header_row + 1, 2)
    sheet.autofilter(header_row, 0, total_row - 1 if performance else header_row, len(headers) - 1)
    widths = [24, 15, 14, 14, 11, 14, 16, 16, 16, 10, 15, 17]
    for col, width in enumerate(widths):
        sheet.set_column(col, col, width)
    sheet.set_landscape()
    sheet.fit_to_pages(1, 0)
    sheet.set_margins(0.3, 0.3, 0.5, 0.5)

    workbook.close()
    output.seek(0)
    filename = f"daily_advisor_performance_{report_date.strftime('%Y%m%d')}.xlsx"
    write_audit("daily_report_exported", "report", None, f"Daily advisor performance for {report_date.isoformat()}")
    db.session.commit()
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/manager/export.xlsx")
@role_required("manager")
def manager_export_excel():
    rows = filtered_quotation_query().order_by(Quotation.created_at.desc()).all()

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    sheet = workbook.add_worksheet("Quotation Data")
    title_fmt = workbook.add_format({"bold": True, "font_size": 16, "align": "left"})
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#EB0A1E", "font_color": "#FFFFFF", "border": 1})
    date_fmt = workbook.add_format({"num_format": "dd/mm/yyyy hh:mm", "border": 1})
    money_fmt = workbook.add_format({"num_format": '0.000 "BHD"', "border": 1})
    cell_fmt = workbook.add_format({"border": 1})
    wrap_fmt = workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})

    sheet.write("A1", "Body & Paint - Quotation Export", title_fmt)
    sheet.write("A2", f"Exported: {local_now().strftime('%d/%m/%Y %H:%M')}")
    headers = [
        "No.", "Date & Time", "Advisor", "Customer Name", "Vehicle Type", "VRN",
        "Damage Area", "Service Offered", "Number of Panels", "Price Quoted",
        "Approved", "Reason for Refusal", "Last Updated",
    ]
    for col, header in enumerate(headers):
        sheet.write(3, col, header, header_fmt)

    for row_idx, q in enumerate(rows, start=4):
        values = [
            q.id,
            q.created_at,
            q.advisor.full_name if q.advisor else "Unknown",
            q.customer_name,
            q.vehicle_type,
            q.vrn,
            q.damage_area,
            q.service_offered,
            q.number_of_panels,
            q.price_quoted,
            q.approved,
            q.reason_for_refusal or "",
            q.updated_at,
        ]
        for col, value in enumerate(values):
            fmt = date_fmt if col in {1, 12} else money_fmt if col == 9 else wrap_fmt if col in {3, 6, 7, 11} else cell_fmt
            sheet.write(row_idx, col, value, fmt)

    sheet.freeze_panes(4, 0)
    sheet.autofilter(3, 0, max(3, 3 + len(rows)), len(headers) - 1)
    widths = [8, 19, 20, 24, 18, 16, 22, 22, 16, 16, 12, 28, 19]
    for col, width in enumerate(widths):
        sheet.set_column(col, col, width)
    workbook.close()
    output.seek(0)
    filename = f"quotation_export_{local_now().strftime('%Y%m%d_%H%M')}.xlsx"
    write_audit("quotation_exported", "report", None, f"Exported {len(rows)} filtered quotations")
    db.session.commit()
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )



@app.route("/manager/users", methods=["GET", "POST"])
@role_required("manager")
def manager_users():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "advisor").strip()
        if not full_name or not username or len(password) < 8 or role not in {"advisor", "manager"}:
            flash("Enter a name, unique username, role, and password of at least 8 characters.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("That username already exists.", "danger")
        else:
            user = User(username=username, full_name=full_name, password_hash=generate_password_hash(password), role=role, active=True)
            db.session.add(user)
            db.session.flush()
            write_audit("user_created", "user", user.id, f"Created {role} account {username}")
            db.session.commit()
            flash(f"User {full_name} created.", "success")
            return redirect(url_for("manager_users"))
    users = User.query.order_by(User.role.asc(), User.full_name.asc()).all()
    rows = []
    for user in users:
        rows.append({"user": user, "quotation_count": Quotation.query.filter_by(advisor_id=user.id).count()})
    return render_template("manager/users.html", rows=rows)


@app.post("/manager/users/<int:user_id>/toggle")
@role_required("manager")
def manager_user_toggle(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
    elif user.id == session.get("user_id"):
        flash("You cannot disable your own account.", "warning")
    else:
        user.active = not user.active
        write_audit("user_enabled" if user.active else "user_disabled", "user", user.id, user.username)
        db.session.commit()
        flash(f"{user.full_name} is now {'active' if user.active else 'disabled'}.", "success")
    return redirect(url_for("manager_users"))


@app.post("/manager/users/<int:user_id>/reset-password")
@role_required("manager")
def manager_user_reset_password(user_id: int):
    user = db.session.get(User, user_id)
    password = request.form.get("password", "")
    if not user:
        flash("User not found.", "danger")
    elif len(password) < 8:
        flash("New password must be at least 8 characters.", "danger")
    else:
        user.password_hash = generate_password_hash(password)
        write_audit("password_reset", "user", user.id, f"Password reset for {user.username}")
        db.session.commit()
        flash(f"Password reset for {user.full_name}.", "success")
    return redirect(url_for("manager_users"))


@app.post("/manager/users/<int:user_id>/delete")
@role_required("manager")
def manager_user_delete(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
    elif user.id == session.get("user_id"):
        flash("You cannot delete your own account.", "warning")
    elif Quotation.query.filter_by(advisor_id=user.id).count() > 0:
        flash("This user has quotation history. Disable the account instead of deleting it.", "warning")
    else:
        name = user.full_name
        username = user.username
        write_audit("user_deleted", "user", user.id, f"Deleted unused account {username}")
        db.session.delete(user)
        db.session.commit()
        flash(f"Unused account {name} deleted.", "success")
    return redirect(url_for("manager_users"))


@app.route("/manager/settings", methods=["GET", "POST"])
@role_required("manager")
def manager_settings():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        value = request.form.get("value", "").strip()
        if category not in DROPDOWN_DEFAULTS or not value:
            flash("Select a valid list and enter a value.", "danger")
        elif DropdownOption.query.filter(func.lower(DropdownOption.category) == category.lower(), func.lower(DropdownOption.value) == value.lower()).first():
            flash("That option already exists.", "warning")
        else:
            max_order = db.session.query(func.max(DropdownOption.sort_order)).filter_by(category=category).scalar() or 0
            option = DropdownOption(category=category, value=value, sort_order=max_order + 1, active=True)
            db.session.add(option)
            db.session.flush()
            write_audit("dropdown_option_created", "dropdown_option", option.id, f"{category}: {value}")
            db.session.commit()
            flash("Dropdown option added.", "success")
            return redirect(url_for("manager_settings"))
    options = DropdownOption.query.order_by(DropdownOption.category.asc(), DropdownOption.sort_order.asc(), DropdownOption.value.asc()).all()
    grouped = defaultdict(list)
    for option in options:
        grouped[option.category].append(option)
    return render_template("manager/settings.html", grouped=grouped)


@app.post("/manager/settings/<int:option_id>/toggle")
@role_required("manager")
def manager_setting_toggle(option_id: int):
    option = db.session.get(DropdownOption, option_id)
    if option:
        option.active = not option.active
        write_audit("dropdown_option_enabled" if option.active else "dropdown_option_disabled", "dropdown_option", option.id, f"{option.category}: {option.value}")
        db.session.commit()
    return redirect(url_for("manager_settings"))


@app.route("/manager/audit")
@role_required("manager")
def manager_audit():
    action = request.args.get("action", "").strip()
    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.created_at.desc()).limit(500).all()
    actions = [row[0] for row in db.session.query(AuditLog.action).distinct().order_by(AuditLog.action.asc()).all()]
    return render_template("manager/audit.html", logs=logs, actions=actions)


@app.route("/manager/activity.json")
@role_required("manager")
def manager_activity_json():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(15).all()
    return jsonify([{
        "time": row.created_at.isoformat(timespec="seconds"),
        "user": row.full_name,
        "action": row.action,
        "details": row.details or "",
    } for row in logs])

@app.route("/health")
def health():
    try:
        db.session.execute(db.select(func.count(User.id))).scalar_one()
        return jsonify(status="ok", database="connected")
    except Exception as exc:
        return jsonify(status="error", database="disconnected", detail=str(exc)), 500


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
