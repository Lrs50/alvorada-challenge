import os
from pathlib import Path

import psycopg

MIGRATIONS = Path(__file__).parent.parent / "sql" / "migrations"

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
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute(RECORD_VERSION, (path.stem,))
            conn.commit()
            applied.append(path.stem)
    return applied


if __name__ == "__main__":
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        print("applied:", migrate(conn) or "nothing to do")
