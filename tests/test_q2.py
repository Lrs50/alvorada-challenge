from datetime import date
from decimal import Decimal
from pathlib import Path

from olist_pipeline.report import query
from olist_pipeline.run import run

FIXTURES = Path(__file__).parent / "fixtures"

JAN = date(2017, 1, 1)
FEB = date(2017, 2, 1)

# Delivered orders only, by purchase month, price only (no freight).
# January has 12 categories, so the top 10 cuts two:
# - juliet ties india at 40.00, and india comes first by name;
# - kilo has 20.00 of sales (its 500.00 freight and its shipped order do not count).
# Products with no category are grouped as 'unknown' (95.00, rank 4).
# hotel is two items: 30.00 + 20.00. The canceled order f3 (900.00) is left out.
# February: alpha and bravo tie at 15.50, so alpha ranks first.
EXPECTED = [
    (JAN, 1, "alpha", Decimal("120.00")),
    (JAN, 2, "bravo", Decimal("110.00")),
    (JAN, 3, "charlie", Decimal("100.00")),
    (JAN, 4, "unknown", Decimal("95.00")),
    (JAN, 5, "delta", Decimal("90.00")),
    (JAN, 6, "echo", Decimal("80.00")),
    (JAN, 7, "foxtrot", Decimal("70.00")),
    (JAN, 8, "golf", Decimal("60.00")),
    (JAN, 9, "hotel", Decimal("50.00")),
    (JAN, 10, "india", Decimal("40.00")),
    (FEB, 1, "alpha", Decimal("15.50")),
    (FEB, 2, "bravo", Decimal("15.50")),
]


def test_top_categories_by_month(conn):
    run(conn, FIXTURES / "categories")
    columns, rows = query(conn, "q2_top_categories_by_month")
    assert columns == ["month", "rank", "product_category", "sales_value"]
    assert rows == EXPECTED
