from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from getpass import getpass

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "quotation_system.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_users_table() -> None:
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('advisor','manager')),
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        db.commit()


def add_user(args: argparse.Namespace) -> None:
    username = (args.username or input("Username: ")).strip().lower()
    full_name = (args.name or input("Full name: ")).strip()
    role = (args.role or input("Role [advisor/manager]: ")).strip().lower()

    if role not in {"advisor", "manager"}:
        raise SystemExit("Role must be 'advisor' or 'manager'.")
    if not username or not full_name:
        raise SystemExit("Username and full name are required.")

    password = args.password
    if not password:
        password = getpass("Password: ")
        confirm = getpass("Confirm password: ")
        if password != confirm:
            raise SystemExit("Passwords do not match.")
    if len(password) < 6:
        raise SystemExit("Password must contain at least 6 characters.")

    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users(username,password_hash,full_name,role,active) VALUES(?,?,?,?,1)",
                (username, generate_password_hash(password), full_name, role),
            )
            db.commit()
    except sqlite3.IntegrityError:
        raise SystemExit(f"Username '{username}' already exists.")

    print(f"Created {role}: {full_name} ({username})")


def list_users(_: argparse.Namespace) -> None:
    with get_db() as db:
        rows = db.execute(
            "SELECT id, username, full_name, role, active FROM users ORDER BY role, full_name"
        ).fetchall()
    if not rows:
        print("No users found.")
        return
    print(f"{'ID':<4} {'USERNAME':<20} {'FULL NAME':<30} {'ROLE':<10} STATUS")
    print("-" * 80)
    for row in rows:
        status = "Active" if row["active"] else "Disabled"
        print(f"{row['id']:<4} {row['username']:<20} {row['full_name']:<30} {row['role']:<10} {status}")


def reset_password(args: argparse.Namespace) -> None:
    username = (args.username or input("Username: ")).strip().lower()
    password = args.password
    if not password:
        password = getpass("New password: ")
        confirm = getpass("Confirm password: ")
        if password != confirm:
            raise SystemExit("Passwords do not match.")
    if len(password) < 6:
        raise SystemExit("Password must contain at least 6 characters.")

    with get_db() as db:
        cur = db.execute(
            "UPDATE users SET password_hash=? WHERE username=?",
            (generate_password_hash(password), username),
        )
        db.commit()
    if cur.rowcount == 0:
        raise SystemExit(f"User '{username}' not found.")
    print(f"Password updated for {username}.")


def set_active(args: argparse.Namespace, active: int) -> None:
    username = args.username.strip().lower()
    with get_db() as db:
        cur = db.execute("UPDATE users SET active=? WHERE username=?", (active, username))
        db.commit()
    if cur.rowcount == 0:
        raise SystemExit(f"User '{username}' not found.")
    print(f"{username} is now {'active' if active else 'disabled'}.")


def main() -> None:
    ensure_users_table()
    parser = argparse.ArgumentParser(description="Manage Cash Quotation System users")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Create a new advisor or manager")
    p_add.add_argument("--username")
    p_add.add_argument("--name")
    p_add.add_argument("--role", choices=["advisor", "manager"])
    p_add.add_argument("--password")
    p_add.set_defaults(func=add_user)

    p_list = sub.add_parser("list", help="List users")
    p_list.set_defaults(func=list_users)

    p_reset = sub.add_parser("reset-password", help="Reset a user's password")
    p_reset.add_argument("username", nargs="?")
    p_reset.add_argument("--password")
    p_reset.set_defaults(func=reset_password)

    p_disable = sub.add_parser("disable", help="Disable a login without deleting history")
    p_disable.add_argument("username")
    p_disable.set_defaults(func=lambda args: set_active(args, 0))

    p_enable = sub.add_parser("enable", help="Re-enable a login")
    p_enable.add_argument("username")
    p_enable.set_defaults(func=lambda args: set_active(args, 1))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
