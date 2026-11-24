import os
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from olist_pipeline.report import query
from olist_pipeline.run import run

URL = os.environ["DATABASE_URL"]
DROP_TEST_DB = "drop database if exists olist_test"
CREATE_TEST_DB = "create database olist_test"


@pytest.fixture
def conn():
    admin = psycopg.connect(URL, autocommit=True)
    admin.execute(DROP_TEST_DB)
    admin.execute(CREATE_TEST_DB)
    with psycopg.connect(make_conninfo(URL, dbname="olist_test")) as c:
        yield c
    admin.execute(DROP_TEST_DB)
    admin.close()


@pytest.fixture
def fixtures():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def answer(conn, fixtures):
    """Run the pipeline on a fixture folder, then return (columns, rows) of one query."""

    def answer(folder, query_name):
        run(conn, fixtures / folder)
        return query(conn, query_name)

    return answer
