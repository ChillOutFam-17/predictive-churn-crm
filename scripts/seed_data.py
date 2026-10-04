"""Seed the local database with demo customers.

Run from the repo root:
    python -m scripts.seed_data              # seeds only if the table is empty
    python -m scripts.seed_data --count 40 --force
"""

import argparse

from src.db import count_customers, init_database
from src.demo_data import insert_demo_customers


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo customers into crm.db")
    parser.add_argument("--count", type=int, default=20, help="number of customers to add")
    parser.add_argument("--force", action="store_true", help="add even if rows already exist")
    args = parser.parse_args()

    init_database()
    existing = count_customers()
    if existing and not args.force:
        print(f"Database already has {existing} customers. Use --force to add more.")
        return

    inserted = insert_demo_customers(args.count)
    print(f"Inserted {inserted} demo customers.")


if __name__ == "__main__":
    main()
