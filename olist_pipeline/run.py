from psycopg.types.json import Jsonb

from olist_pipeline.load import load
from olist_pipeline.migrate import migrate
from olist_pipeline.transform import transform

START_RUN = "insert into ops.pipeline_runs default values returning run_id"
CORE_COUNT = "select count(*) from core.{}"
REJECT_COUNTS = "select source_table, count(*) from ops.reject where run_id = %s group by 1"
FINISH_RUN = """
update ops.pipeline_runs
set finished_at = now(), status = 'succeeded',
    rows_read = %s, rows_loaded = %s, rows_rejected = %s, details = %s
where run_id = %s
"""
FAIL_RUN = """
update ops.pipeline_runs set finished_at = now(), status = 'failed', error = %s where run_id = %s
"""


def run(conn, data_dir):
    """Migrate, load and transform. Log the run, and raise if it fails."""
    applied = migrate(conn)
    print(
        f"Applied {len(applied)} migrations" if applied else "Migrations are up to date", flush=True
    )
    run_id = conn.execute(START_RUN).fetchone()[0]
    conn.commit()
    try:
        read = load(conn, data_dir)
        print("Cleaning and typing the data...", flush=True)
        transform(conn, run_id)
        rejected = dict(conn.execute(REJECT_COUNTS, (run_id,)).fetchall())
        details = {}
        for table, rows_read in read.items():
            loaded = conn.execute(CORE_COUNT.format(table)).fetchone()[0]
            details[table] = {
                "read": rows_read,
                "loaded": loaded,
                "rejected": rejected.get(table, 0),
            }
        totals = [sum(d[key] for d in details.values()) for key in ("read", "loaded", "rejected")]
        conn.execute(FINISH_RUN, (*totals, Jsonb(details), run_id))
        print(f"Cleaned and typed the data: {totals[2]:,} rows rejected", flush=True)
    except Exception as error:
        conn.rollback()
        conn.execute(FAIL_RUN, (str(error), run_id))
        conn.commit()
        raise
    conn.commit()
    return run_id, details
