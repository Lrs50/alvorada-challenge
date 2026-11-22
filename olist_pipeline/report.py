import csv
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).parent.parent
QUERIES = ROOT / "sql" / "queries"
RESULTS = ROOT / "results"


def query(conn, name):
    """Run sql/queries/<name>.sql and return its column names and rows."""
    cur = conn.execute((QUERIES / f"{name}.sql").read_text(encoding="utf-8"))
    return [column.name for column in cur.description], cur.fetchall()


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        columns, rows = query(conn, "q1_sales_by_month_state")
    path = RESULTS / "q1_sales_by_month_state.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)
    print(f"{path.name}: {len(rows)} rows")
