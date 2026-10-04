"""SQLite data layer: connection handling and CRUD for the customers table."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

import pandas as pd

from src.config import DB_PATH

# (customer_name, plan_type, monthly_usage_hours, support_tickets, account_age_months)
CustomerRow = tuple[str, str, float, int, int]

_INSERT_SQL = """
    INSERT INTO customers
        (customer_name, plan_type, monthly_usage_hours,
         support_tickets, account_age_months)
    VALUES (?, ?, ?, ?, ?)
"""


@contextmanager
def connect(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Path = DB_PATH) -> None:
    """Create the customers table if it does not exist yet."""
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                monthly_usage_hours REAL NOT NULL,
                support_tickets INTEGER NOT NULL,
                account_age_months INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def insert_customer(
    customer_name: str,
    plan_type: str,
    monthly_usage_hours: float,
    support_tickets: int,
    account_age_months: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a new customer record."""
    with connect(db_path) as conn:
        conn.execute(
            _INSERT_SQL,
            (
                customer_name.strip(),
                plan_type,
                monthly_usage_hours,
                support_tickets,
                account_age_months,
            ),
        )


def insert_customers(rows: Sequence[CustomerRow], db_path: Path = DB_PATH) -> int:
    """Bulk-insert customer rows. Returns how many were inserted."""
    with connect(db_path) as conn:
        conn.executemany(_INSERT_SQL, rows)
    return len(rows)


def fetch_all_customers(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Load every customer row as a DataFrame, newest first."""
    with connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM customers ORDER BY id DESC", conn)


def delete_customer(customer_id: int, db_path: Path = DB_PATH) -> None:
    """Remove a single customer by primary key."""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))


def count_customers(db_path: Path = DB_PATH) -> int:
    """Return the number of customer rows."""
    with connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
