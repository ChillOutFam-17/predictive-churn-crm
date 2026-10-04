"""Demo customer generation and first-run seeding."""

import random
from pathlib import Path

from src.config import DB_PATH, PLAN_TYPES
from src.db import CustomerRow, count_customers, insert_customers
from src.scoring import expected_monthly_usage

COMPANY_PREFIXES = [
    "Acme", "Nova", "BlueSky", "TechFlow", "DataPeak", "CloudNine",
    "PixelWorks", "Zenith", "BrightPath", "CoreLogic", "SwiftScale",
    "NorthStar", "Pulse", "Vertex", "Ironclad", "Summit", "Horizon",
]
COMPANY_SUFFIXES = ["Labs", "Inc", "Corp", "Solutions", "Systems", "Co", "Analytics"]

# Higher-tier plans tend to have heavier product usage.
PLAN_USAGE_BOOST = {"Basic": 0.0, "Pro": 5.0, "Enterprise": 12.0}


def _random_demo_name(rng: random.Random, used_names: set[str]) -> str:
    """Build a unique fake company name."""
    for _ in range(50):
        name = f"{rng.choice(COMPANY_PREFIXES)} {rng.choice(COMPANY_SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    fallback = f"Demo Customer {rng.randint(1000, 9999)}"
    used_names.add(fallback)
    return fallback


def _random_realistic_metrics(rng: random.Random) -> tuple[str, float, int, int]:
    """Return (plan_type, monthly_usage_hours, support_tickets, account_age_months)."""
    profile = rng.choices(["healthy", "medium", "high_risk"], weights=[40, 35, 25], k=1)[0]
    plan_type = rng.choices(PLAN_TYPES, weights=[50, 35, 15], k=1)[0]
    account_age_months = rng.randint(1, 36)
    expected_usage = expected_monthly_usage(account_age_months)

    if profile == "healthy":
        support_tickets = rng.randint(0, 1)
        usage = rng.uniform(expected_usage, expected_usage + 25)
    elif profile == "medium":
        support_tickets = rng.randint(2, 4)
        usage = rng.uniform(expected_usage * 0.35, expected_usage * 0.9)
    else:
        support_tickets = rng.randint(4, 8)
        usage = rng.uniform(0.5, expected_usage * 0.35)

    usage += PLAN_USAGE_BOOST[plan_type] * rng.uniform(0.4, 1.0)
    return plan_type, round(usage, 1), support_tickets, account_age_months


def generate_demo_customers(count: int = 20, seed: int | None = None) -> list[CustomerRow]:
    """Build fake customer rows. Pass a seed for reproducible output."""
    rng = random.Random(seed)
    used_names: set[str] = set()
    rows: list[CustomerRow] = []
    for _ in range(count):
        plan_type, usage, tickets, age = _random_realistic_metrics(rng)
        rows.append((_random_demo_name(rng, used_names), plan_type, usage, tickets, age))
    return rows


def insert_demo_customers(
    count: int = 20, db_path: Path = DB_PATH, seed: int | None = None
) -> int:
    """Insert generated demo customers. Returns how many were inserted."""
    return insert_customers(generate_demo_customers(count, seed), db_path)


def seed_if_empty(count: int = 20, db_path: Path = DB_PATH) -> int:
    """Insert demo data only when the table is empty. Returns rows inserted."""
    if count_customers(db_path) > 0:
        return 0
    return insert_demo_customers(count, db_path)
