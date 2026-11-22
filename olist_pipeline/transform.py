from pathlib import Path

SQL = Path(__file__).parent.parent / "sql" / "transform"
TABLES = ["customers", "products", "orders", "order_items", "order_payments"]
TRUNCATE = (
    "truncate core.customers, core.products, core.orders, core.order_items, core.order_payments"
)


def transform(conn, run_id):
    """Rebuild the core tables from raw. Rows that fail a check go to ops.reject."""
    with conn.transaction():
        conn.execute(TRUNCATE)
        for table in TABLES:
            conn.execute((SQL / f"{table}.sql").read_text(encoding="utf-8"), (run_id,))
