import pytest

from olist_pipeline.load import load
from olist_pipeline.migrate import migrate

COUNTS = {"customers": 3, "orders": 3, "order_items": 4, "order_payments": 4, "products": 2}


def count(conn, table):
    return conn.execute(f"select count(*) from raw.{table}").fetchone()[0]


def test_load_copies_every_row(conn, fixtures):
    migrate(conn)
    assert load(conn, fixtures) == COUNTS
    assert {t: count(conn, t) for t in COUNTS} == COUNTS


def test_values_stay_text_and_blanks_are_null(conn, fixtures):
    migrate(conn)
    load(conn, fixtures)
    price = conn.execute("select price from raw.order_items where order_id = 'o2'").fetchone()
    delivered = conn.execute(
        "select order_delivered_customer_date from raw.orders where order_id = 'o2'"
    ).fetchone()
    assert price == ("15.50",)
    assert delivered == (None,)


def test_reload_gives_same_counts(conn, fixtures):
    migrate(conn)
    load(conn, fixtures)
    assert load(conn, fixtures) == COUNTS
    assert {t: count(conn, t) for t in COUNTS} == COUNTS


def test_bad_file_rolls_back_the_whole_load(conn, fixtures):
    migrate(conn)
    load(conn, fixtures)
    with pytest.raises(ValueError):
        load(conn, fixtures / "bad")
    assert count(conn, "customers") == COUNTS["customers"]
    assert count(conn, "orders") == COUNTS["orders"]
