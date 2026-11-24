from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
SQL = ROOT / "sql"
RESULTS = ROOT / "results"
TABLES = ["customers", "products", "orders", "order_items", "order_payments"]
