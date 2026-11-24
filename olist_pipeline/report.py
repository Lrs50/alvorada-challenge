import csv
import json

from olist_pipeline.config import RESULTS, ROOT, SQL
from olist_pipeline.db import read_sql

QUERIES = SQL / "queries"
DASHBOARD = ROOT / "olist_pipeline" / "dashboard_template.html"


def query(conn, name):
    """Run sql/queries/<name>.sql and return its column names and rows."""
    cur = conn.execute(read_sql(QUERIES, name))
    return [column.name for column in cur.description], cur.fetchall()


def render_dashboard(results):
    """Put the query results into the dashboard template as JSON."""
    data = json.dumps(results, default=str).replace("</", "<\\/")
    return DASHBOARD.read_text(encoding="utf-8").replace("__DATA__", data)


def report(conn, results_dir=RESULTS):
    """Run every query in sql/queries, write results/*.csv and the dashboard, return the results."""
    results_dir.mkdir(exist_ok=True)
    results = {}
    for path in sorted(QUERIES.glob("*.sql")):
        columns, rows = query(conn, path.stem)
        results[path.stem] = {"columns": columns, "rows": rows}
        with (results_dir / f"{path.stem}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(columns)
            writer.writerows(rows)
    with (results_dir / "dashboard.html").open("w", newline="", encoding="utf-8") as f:
        f.write(render_dashboard(results))
    return results
