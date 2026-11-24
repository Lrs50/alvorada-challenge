import os

import psycopg


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"])


def read_sql(folder, name):
    """Return the text of <folder>/<name>.sql."""
    return (folder / f"{name}.sql").read_text(encoding="utf-8")
