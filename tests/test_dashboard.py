import json
import re
from datetime import date
from decimal import Decimal

from olist_pipeline.report import render_dashboard

RESULTS = {
    "q1_sales_by_month_state": {
        "columns": ["month", "customer_state", "sales_value", "orders", "avg_ticket"],
        "rows": [[date(2017, 1, 1), "SP", Decimal("75.00"), 2, Decimal("37.50")]],
    },
    "q2_top_categories_by_month": {
        "columns": ["month", "rank", "product_category", "sales_value"],
        "rows": [[date(2017, 1, 1), 1, "</script><b>x", Decimal("120.00")]],
    },
}


def test_page_embeds_the_results_exactly():
    page = render_dashboard(RESULTS)
    assert "__DATA__" not in page
    embedded = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S)
    assert embedded is not None
    assert json.loads(embedded.group(1)) == {
        "q1_sales_by_month_state": {
            "columns": ["month", "customer_state", "sales_value", "orders", "avg_ticket"],
            "rows": [["2017-01-01", "SP", "75.00", 2, "37.50"]],
        },
        "q2_top_categories_by_month": {
            "columns": ["month", "rank", "product_category", "sales_value"],
            "rows": [["2017-01-01", 1, "</script><b>x", "120.00"]],
        },
    }


def test_data_cannot_close_the_script_tag():
    page = render_dashboard(RESULTS)
    assert page.count("</script>") == 2
