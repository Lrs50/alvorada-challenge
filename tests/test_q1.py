from datetime import date
from decimal import Decimal

# Delivered orders only, by purchase month, price only (no freight).
# Jan SP: o1 (10 + 20 + 5) + o2 (40) = 75.00 over 2 orders.
# Jan RJ: o3 (100) + o8 (60, bought 31 Jan, delivered in Feb) = 160.00 over 2 orders.
# Feb SP: o4 = 12.50 over 1 order. Feb RJ: o5 (30 + 20) = 50.00 over 1 order.
# o6 (shipped) and o7 (canceled) are left out. o1 and o5 have two payments each.
EXPECTED = [
    (date(2017, 1, 1), "RJ", Decimal("160.00"), 2, Decimal("80.00")),
    (date(2017, 1, 1), "SP", Decimal("75.00"), 2, Decimal("37.50")),
    (date(2017, 2, 1), "RJ", Decimal("50.00"), 1, Decimal("50.00")),
    (date(2017, 2, 1), "SP", Decimal("12.50"), 1, Decimal("12.50")),
]


def test_sales_by_month_and_state(answer):
    columns, rows = answer("sales", "q1_sales_by_month_state")
    assert columns == ["month", "customer_state", "sales_value", "orders", "avg_ticket"]
    assert rows == EXPECTED
