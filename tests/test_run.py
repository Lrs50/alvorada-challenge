import psycopg
import pytest

from olist_pipeline import transform
from olist_pipeline.run import run

RUN_ROW = """
select status, finished_at is not null, rows_read, rows_loaded, rows_rejected, details, error
from ops.pipeline_runs where run_id = %s
"""
CORE_ORDERS = "select count(*) from core.orders"
RAW_ORDERS = "select count(*) from raw.orders"


def test_successful_run_is_logged(conn, fixtures):
    run_id, _ = run(conn, fixtures)
    status, finished, read, loaded, rejected, details, error = conn.execute(
        RUN_ROW, (run_id,)
    ).fetchone()
    assert (status, finished, read, loaded, rejected, error) == ("succeeded", True, 16, 16, 0, None)
    assert details["orders"] == {"read": 3, "loaded": 3, "rejected": 0}
    assert details["order_items"] == {"read": 4, "loaded": 4, "rejected": 0}


def test_rejected_rows_are_counted_per_table(conn, fixtures):
    run_id, _ = run(conn, fixtures / "dirty")
    status, _, read, loaded, rejected, details, _ = conn.execute(RUN_ROW, (run_id,)).fetchone()
    assert (status, read, loaded, rejected) == ("succeeded", 25, 10, 15)
    assert details["orders"] == {"read": 6, "loaded": 2, "rejected": 4}
    assert details["customers"] == {"read": 5, "loaded": 2, "rejected": 3}


def test_failed_run_is_logged_and_raised(conn, fixtures):
    with pytest.raises(ValueError):
        run(conn, fixtures / "bad")
    status, finished, read, loaded, rejected, details, error = conn.execute(
        RUN_ROW, (1,)
    ).fetchone()
    assert (status, finished, read, loaded, rejected, details) == (
        "failed",
        True,
        None,
        None,
        None,
        None,
    )
    assert "raw.orders" in error


def test_rerun_logs_a_new_run_and_keeps_the_data(conn, fixtures):
    first, _ = run(conn, fixtures)
    second, _ = run(conn, fixtures)
    assert second != first
    assert conn.execute(CORE_ORDERS).fetchone() == (3,)
    statuses = conn.execute("select status from ops.pipeline_runs order by run_id").fetchall()
    assert statuses == [("succeeded",), ("succeeded",)]


def test_failed_transform_keeps_the_previous_core_and_the_new_raw(conn, fixtures, monkeypatch):
    first, _ = run(conn, fixtures)
    real_read_sql = transform.read_sql

    def failing_read_sql(folder, name):
        return "select %s::int / 0" if name == "orders" else real_read_sql(folder, name)

    monkeypatch.setattr(transform, "read_sql", failing_read_sql)
    with pytest.raises(psycopg.errors.DivisionByZero):
        run(conn, fixtures / "sales")
    status, finished, *_, error = conn.execute(RUN_ROW, (first + 1,)).fetchone()
    assert (status, finished) == ("failed", True)
    assert "division by zero" in error
    assert conn.execute(RUN_ROW, (first,)).fetchone()[0] == "succeeded"
    assert conn.execute(RAW_ORDERS).fetchone() == (8,)
    assert conn.execute(CORE_ORDERS).fetchone() == (3,)
