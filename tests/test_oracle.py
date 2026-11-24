from olist_pipeline.oracle import q1, q2, q3

# Same three orders and hand-calculated answers as test_worked_example.py, in cents.


def test_sales_by_month_and_state(fixtures):
    assert q1(fixtures / "worked_example") == [("2017-01-01", "SP", 15000, 2, 7500)]


def test_top_categories(fixtures):
    assert q2(fixtures / "worked_example") == [
        ("2017-01-01", 1, "livros", 10000),
        ("2017-01-01", 2, "papelaria", 5000),
    ]


def test_payment_divergences(fixtures):
    assert q3(fixtures / "worked_example") == [
        ("c", "canceled", 3300, 0, -3300, "no payment"),
        ("b", "delivered", 5500, 5498, -2, "paid less"),
    ]
