from psycopg import sql

from olist_pipeline.config import SQL, TABLES
from olist_pipeline.db import read_sql

TRUNCATE = sql.SQL("truncate {}").format(
    sql.SQL(", ").join(sql.Identifier("core", table) for table in TABLES)
)


def transform(conn, run_id):
    """Rebuild the core tables from raw. Rows that fail a check go to ops.reject."""
    with conn.transaction():
        conn.execute(TRUNCATE)
        for table in TABLES:
            conn.execute(read_sql(SQL / "transform", table), (run_id,))
