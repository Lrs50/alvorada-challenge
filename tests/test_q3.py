from decimal import Decimal
from pathlib import Path

from olist_pipeline.report import query
from olist_pipeline.run import run

FIXTURES = Path(__file__).parent / "fixtures"

# Billed = items + freight; difference = paid - billed; flagged when |difference| > 0.01,
# or when the order has no payment at all. Every status is checked.
#
# Not flagged:
#   m1  billed 35.00 (2 items), paid 35.00 (2 payments). A direct items-to-payments join
#       would count each item twice, so this order catches that mistake.
#   m2  paid 50.01 on 50.00 (+0.01, the boundary)     m9  paid 19.99 on 20.00 (-0.01)
#   m8  canceled, no items, one payment of 0.00 (0 paid on 0 billed)
# Flagged, largest difference first (ties by order id):
EXPECTED = [
    ("m6", "delivered", Decimal("40.00"), Decimal("0"), Decimal("-40.00"), "no payment"),
    ("m5", "canceled", Decimal("30.00"), Decimal("45.00"), Decimal("15.00"), "paid more"),
    ("m7", "canceled", Decimal("0"), Decimal("12.00"), Decimal("12.00"), "no items"),
    ("m4", "shipped", Decimal("100.00"), Decimal("90.00"), Decimal("-10.00"), "paid less"),
    ("m10", "created", Decimal("20.00"), Decimal("19.98"), Decimal("-0.02"), "paid less"),
    ("m3", "delivered", Decimal("50.00"), Decimal("50.02"), Decimal("0.02"), "paid more"),
]


def test_payment_divergences(conn):
    run(conn, FIXTURES / "payments")
    columns, rows = query(conn, "q3_payment_divergences")
    assert columns == [
        "order_id",
        "order_status",
        "items_total",
        "paid_total",
        "difference",
        "reason",
    ]
    assert rows == EXPECTED
