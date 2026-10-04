import pytest

from src.db import (
    count_customers,
    delete_customer,
    fetch_all_customers,
    init_database,
    insert_customer,
)


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_database(path)
    return path


def test_insert_and_fetch_round_trip(db_path):
    insert_customer("  Acme Labs ", "Pro", 12.5, 2, 6, db_path=db_path)
    df = fetch_all_customers(db_path)
    assert len(df) == 1
    assert df.iloc[0]["customer_name"] == "Acme Labs"  # whitespace stripped
    assert df.iloc[0]["monthly_usage_hours"] == 12.5


def test_delete_removes_only_the_target_row(db_path):
    insert_customer("A", "Basic", 1.0, 0, 1, db_path=db_path)
    insert_customer("B", "Basic", 1.0, 0, 1, db_path=db_path)
    first_id = int(fetch_all_customers(db_path).iloc[-1]["id"])
    delete_customer(first_id, db_path)
    assert list(fetch_all_customers(db_path)["customer_name"]) == ["B"]


def test_count_customers(db_path):
    assert count_customers(db_path) == 0
    insert_customer("A", "Basic", 1.0, 0, 1, db_path=db_path)
    assert count_customers(db_path) == 1
