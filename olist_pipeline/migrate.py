from olist_pipeline.config import SQL
from olist_pipeline.db import read_sql

MIGRATIONS = SQL / "migrations"

CREATE_MIGRATIONS_TABLE = """
create schema if not exists ops;
create table if not exists ops.schema_migrations (
    version text primary key,
    applied_at timestamptz not null default now()
);
"""
APPLIED_VERSIONS = "select version from ops.schema_migrations"
RECORD_VERSION = "insert into ops.schema_migrations (version) values (%s)"


def migrate(conn):
    """Apply pending migrations in name order and return the versions applied."""
    conn.execute(CREATE_MIGRATIONS_TABLE)
    conn.commit()
    done = {row[0] for row in conn.execute(APPLIED_VERSIONS)}
    applied = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.stem not in done:
            conn.execute(read_sql(MIGRATIONS, path.stem))
            conn.execute(RECORD_VERSION, (path.stem,))
            conn.commit()
            applied.append(path.stem)
    return applied
