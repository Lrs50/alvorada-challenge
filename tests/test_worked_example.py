from datetime import date
from decimal import Decimal

from olist_pipeline.report import query
from olist_pipeline.run import run

# Three orders in January 2017, all from SP.
#   a  delivered, books: items 60 + 40, freight 6 + 4, paid 70 + 40 = 110 (reconciled).
#   b  delivered, stationery: item 50, freight 5, paid 54.98 (0.02 short).
#   c  canceled, books: item 30, freight 3, no payment rows.
# Canceled orders are out of sales and rankings but still checked for payments.
Q1 = [(date(2017, 1, 1), "SP", Decimal("150.00"), 2, Decimal("75.00"))]
Q2 = [
    (date(2017, 1, 1), 1, "livros", Decimal("100.00")),
    (date(2017, 1, 1), 2, "papelaria", Decimal("50.00")),
]
Q3 = [
    ("c", "canceled", Decimal("33.00"), Decimal("0"), Decimal("-33.00"), "no payment"),
    ("b", "delivered", Decimal("55.00"), Decimal("54.98"), Decimal("-0.02"), "paid less"),
]


def answers(conn):
    names = ["q1_sales_by_month_state", "q2_top_categories_by_month", "q3_payment_divergences"]
    return [query(conn, name)[1] for name in names]


def test_worked_example(conn, fixtures):
    run(conn, fixtures / "worked_example")
    assert answers(conn) == [Q1, Q2, Q3]


def test_rerun_keeps_the_answers(conn, fixtures):
    run(conn, fixtures / "worked_example")
    run(conn, fixtures / "worked_example")
    assert answers(conn) == [Q1, Q2, Q3]
