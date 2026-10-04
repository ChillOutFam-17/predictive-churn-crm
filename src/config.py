"""Shared configuration constants."""

from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"
PLAN_TYPES = ["Basic", "Pro", "Enterprise"]
