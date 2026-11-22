import os

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

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
