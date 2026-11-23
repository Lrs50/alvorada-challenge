from pathlib import Path

from audit.oracle import q1, q2, q3

WORKED_EXAMPLE = Path(__file__).parent / "fixtures" / "worked_example"

# Same three orders and hand-calculated answers as test_worked_example.py, in cents.


def test_sales_by_month_and_state():
    assert q1(WORKED_EXAMPLE) == [("2017-01-01", "SP", 15000, 2, 7500)]


def test_top_categories():
    assert q2(WORKED_EXAMPLE) == [
        ("2017-01-01", 1, "livros", 10000),
        ("2017-01-01", 2, "papelaria", 5000),
    ]


def test_payment_divergences():
    assert q3(WORKED_EXAMPLE) == [
        ("c", "canceled", 3300, 0, -3300, "no payment"),
        ("b", "delivered", 5500, 5498, -2, "paid less"),
    ]
