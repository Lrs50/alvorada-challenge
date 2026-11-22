import csv
import os
from pathlib import Path

import psycopg
from psycopg import sql

DATA = Path(__file__).parent.parent / "data"
FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "products": "olist_products_dataset.csv",
}

RAW_COLUMNS = """
select column_name
from information_schema.columns
where table_schema = 'raw' and table_name = %s and column_name <> 'loaded_at'
order by ordinal_position
"""
TRUNCATE = sql.SQL("truncate raw.{table}")
COPY = sql.SQL("copy raw.{table} ({columns}) from stdin (format csv, header)")


def load(conn, data_dir):
    """Replace the contents of every raw table with its CSV, in one transaction."""
    counts = {}
    with conn.transaction():
        for table, name in FILES.items():
            path = Path(data_dir) / name
            with open(path, newline="", encoding="utf-8") as f:
                header = next(csv.reader(f))
            expected = [row[0] for row in conn.execute(RAW_COLUMNS, (table,))]
            if header != expected:
                raise ValueError(f"{name}: columns {header} do not match raw.{table} {expected}")
            table_id = sql.Identifier(table)
            columns = sql.SQL(", ").join(map(sql.Identifier, header))
            conn.execute(TRUNCATE.format(table=table_id))
            with conn.cursor() as cur:
                with cur.copy(COPY.format(table=table_id, columns=columns)) as copy:
                    with open(path, "rb") as f:
                        while block := f.read(65536):
                            copy.write(block)
                counts[table] = cur.rowcount
    return counts


if __name__ == "__main__":
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        for table, rows in load(conn, DATA).items():
            print(f"{table}: {rows}")
