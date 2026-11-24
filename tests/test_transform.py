from decimal import Decimal

from olist_pipeline.load import load
from olist_pipeline.migrate import migrate
from olist_pipeline.run import START_RUN
from olist_pipeline.transform import transform

CLEAN = {"customers": 3, "orders": 3, "order_items": 4, "order_payments": 4, "products": 2}
DIRTY = {"customers": 2, "orders": 2, "order_items": 2, "order_payments": 2, "products": 2}
DIRTY_REJECTS = {
    ("customers", "blank customer_id"),
    ("customers", "blank customer_state"),
    ("customers", "duplicate customer_id"),
    ("products", "duplicate product_id"),
    ("orders", "duplicate order_id"),
    ("orders", "invalid order_delivered_customer_date"),
    ("orders", "invalid order_purchase_timestamp"),
    ("orders", "unknown customer_id"),
    ("order_items", "duplicate order item"),
    ("order_items", "invalid price"),
    ("order_items", "unknown order_id"),
    ("order_items", "unknown product_id"),
    ("order_payments", "duplicate order payment"),
    ("order_payments", "invalid payment_value"),
    ("order_payments", "unknown order_id"),
}


def new_run(conn):
    run_id = conn.execute(START_RUN).fetchone()[0]
    conn.commit()
    return run_id


def prepare(conn, data_dir):
    migrate(conn)
    load(conn, data_dir)
    return new_run(conn)


def core_counts(conn):
    return {t: conn.execute(f"select count(*) from core.{t}").fetchone()[0] for t in CLEAN}


def test_clean_data_loads_everything(conn, fixtures):
    transform(conn, prepare(conn, fixtures))
    assert core_counts(conn) == CLEAN
    assert conn.execute("select count(*) from ops.reject").fetchone() == (0,)
    category = conn.execute(
        "select product_category_name from core.products where product_id = 'p2'"
    )
    price = conn.execute("select price from core.order_items where order_id = 'o2'")
    delivered = conn.execute(
        "select order_delivered_customer_date from core.orders where order_id = 'o2'"
    )
    assert category.fetchone() == (None,)
    assert price.fetchone() == (Decimal("15.50"),)
    assert delivered.fetchone() == (None,)


def test_bad_rows_are_rejected_with_a_reason(conn, fixtures):
    transform(conn, prepare(conn, fixtures / "dirty"))
    assert core_counts(conn) == DIRTY
    rejects = conn.execute("select source_table, reason from ops.reject").fetchall()
    assert len(rejects) == 15
    assert set(rejects) == DIRTY_REJECTS
    bad_price = conn.execute(
        "select row_data ->> 'price' from ops.reject where reason = 'invalid price'"
    )
    assert bad_price.fetchone() == ("abc",)


def test_text_is_trimmed(conn, fixtures):
    transform(conn, prepare(conn, fixtures / "dirty"))
    state = conn.execute("select customer_state from core.customers where customer_id = 'c2'")
    category = conn.execute(
        "select product_category_name from core.products where product_id = 'p1'"
    )
    assert state.fetchone() == ("RJ",)
    assert category.fetchone() == ("perfumaria",)


def test_rerun_keeps_core_and_logs_rejects_per_run(conn, fixtures):
    first = prepare(conn, fixtures / "dirty")
    transform(conn, first)
    second = new_run(conn)
    transform(conn, second)
    assert core_counts(conn) == DIRTY
    per_run = conn.execute("select run_id, count(*) from ops.reject group by run_id").fetchall()
    assert dict(per_run) == {first: 15, second: 15}
