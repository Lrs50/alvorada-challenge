from olist_pipeline.migrate import migrate

VERSIONS = ["001_raw_tables", "002_core_tables", "003_ops_tables"]
TABLES = ["orders", "order_items", "order_payments", "customers", "products"]

ALL_TABLES = """
select table_schema, table_name
from information_schema.tables
where table_schema in ('raw', 'core', 'ops')
"""
RAW_TABLES_WITH_LOADED_AT = """
select table_name
from information_schema.columns
where table_schema = 'raw' and column_name = 'loaded_at'
"""
COLUMNS = """
select column_name
from information_schema.columns
where table_schema = %s and table_name = %s
"""
PRIMARY_KEY = """
select kcu.column_name
from information_schema.table_constraints tc
join information_schema.key_column_usage kcu
  on kcu.constraint_name = tc.constraint_name and kcu.table_schema = tc.table_schema
where tc.constraint_type = 'PRIMARY KEY'
  and tc.table_schema = %s and tc.table_name = %s
order by kcu.ordinal_position
"""


def primary_key(conn, schema, table):
    return [r[0] for r in conn.execute(PRIMARY_KEY, (schema, table)).fetchall()]


def test_second_run_applies_nothing(conn):
    assert migrate(conn) == VERSIONS
    assert migrate(conn) == []


def test_tables_exist(conn):
    migrate(conn)
    found = set(conn.execute(ALL_TABLES).fetchall())
    expected = {(s, t) for s in ("raw", "core") for t in TABLES}
    expected |= {("ops", "reject"), ("ops", "pipeline_runs"), ("ops", "schema_migrations")}
    assert expected == found


def test_primary_keys(conn):
    migrate(conn)
    assert primary_key(conn, "core", "orders") == ["order_id"]
    assert primary_key(conn, "core", "customers") == ["customer_id"]
    assert primary_key(conn, "core", "products") == ["product_id"]
    assert primary_key(conn, "core", "order_items") == ["order_id", "order_item_id"]
    assert primary_key(conn, "core", "order_payments") == ["order_id", "payment_sequential"]


def test_payments_keep_installments(conn):
    migrate(conn)
    columns = {r[0] for r in conn.execute(COLUMNS, ("core", "order_payments")).fetchall()}
    assert "payment_installments" in columns


def test_raw_tables_record_arrival_time(conn):
    migrate(conn)
    rows = conn.execute(RAW_TABLES_WITH_LOADED_AT).fetchall()
    assert {r[0] for r in rows} == set(TABLES)
