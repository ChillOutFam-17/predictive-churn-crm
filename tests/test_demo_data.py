from src.config import PLAN_TYPES
from src.db import count_customers, init_database
from src.demo_data import generate_demo_customers, seed_if_empty


def test_generation_is_reproducible_with_a_seed():
    assert generate_demo_customers(20, seed=1) == generate_demo_customers(20, seed=1)


def test_generated_rows_are_valid_and_names_unique():
    rows = generate_demo_customers(20, seed=7)
    assert len(rows) == 20
    assert len({row[0] for row in rows}) == 20
    for _, plan, usage, tickets, age in rows:
        assert plan in PLAN_TYPES
        assert usage > 0 and tickets >= 0 and 1 <= age <= 36


def test_seed_if_empty_only_seeds_once(tmp_path):
    path = tmp_path / "seed.db"
    init_database(path)
    assert seed_if_empty(10, path) == 10
    assert seed_if_empty(10, path) == 0
    assert count_customers(path) == 10
