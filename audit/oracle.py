import csv
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
KINDS = {
    "q1_sales_by_month_state": ("text", "text", "money", "int", "money"),
    "q2_top_categories_by_month": ("text", "int", "text", "money"),
    "q3_payment_divergences": ("text", "text", "money", "money", "money", "text"),
}


def read(data_dir, name, columns):
    path = data_dir / f"olist_{name}_dataset.csv"
    return pd.read_csv(path, usecols=columns, dtype=str)


def cents(values):
    return (values.astype(float) * 100).round().astype("int64")


def delivered_items(data_dir):
    orders = read(
        data_dir,
        "orders",
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
    )
    orders = orders[orders["order_status"] == "delivered"].copy()
    orders["month"] = orders["order_purchase_timestamp"].str[:7] + "-01"
    items = read(data_dir, "order_items", ["order_id", "product_id", "price"])
    items["price"] = cents(items["price"])
    return orders.merge(items, on="order_id")


def q1(data_dir):
    customers = read(data_dir, "customers", ["customer_id", "customer_state"])
    sales = delivered_items(data_dir).merge(customers, on="customer_id")
    grouped = sales.groupby(["month", "customer_state"]).agg(
        sales=("price", "sum"), orders=("order_id", "nunique")
    )
    return [
        (month, state, row.sales, row.orders, (2 * row.sales + row.orders) // (2 * row.orders))
        for (month, state), row in grouped.iterrows()
    ]


def q2(data_dir):
    products = read(data_dir, "products", ["product_id", "product_category_name"])
    sales = delivered_items(data_dir).merge(products, on="product_id", how="left")
    sales["category"] = sales["product_category_name"].fillna("unknown")
    totals = sales.groupby(["month", "category"], as_index=False)["price"].sum()
    totals = totals.sort_values(["month", "price", "category"], ascending=[True, False, True])
    totals["rank"] = totals.groupby("month").cumcount() + 1
    top = totals[totals["rank"] <= 10]
    return [(r.month, r.rank, r.category, r.price) for r in top.itertuples()]


def q3(data_dir):
    orders = read(data_dir, "orders", ["order_id", "order_status"])
    items = read(data_dir, "order_items", ["order_id", "price", "freight_value"])
    billed = (
        (cents(items["price"]) + cents(items["freight_value"])).groupby(items["order_id"]).sum()
    )
    payments = read(data_dir, "order_payments", ["order_id", "payment_value"])
    paid = cents(payments["payment_value"]).groupby(payments["order_id"]).sum()
    rows = []
    for order_id, status in orders.itertuples(index=False):
        items_total = billed.get(order_id, 0)
        paid_total = paid.get(order_id, 0)
        difference = paid_total - items_total
        if order_id not in paid.index:
            reason = "no payment"
        elif abs(difference) <= 1:
            continue
        elif order_id not in billed.index:
            reason = "no items"
        else:
            reason = "paid more" if difference > 0 else "paid less"
        rows.append((order_id, status, items_total, paid_total, difference, reason))
    return sorted(rows, key=lambda row: (-abs(row[4]), row[0]))


def published(name):
    convert = {"text": str, "int": int, "money": lambda cell: int(Decimal(cell) * 100)}
    with open(RESULTS / f"{name}.csv", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        kinds = KINDS[name]
        return [tuple(convert[k](cell) for k, cell in zip(kinds, r, strict=True)) for r in reader]


def main(data_dir=DATA):
    differences = 0
    for name, compute in [
        ("q1_sales_by_month_state", q1),
        ("q2_top_categories_by_month", q2),
        ("q3_payment_divergences", q3),
    ]:
        oracle = compute(data_dir)
        sql = published(name)
        if oracle == sql:
            print(f"{name}: {len(sql)} rows match")
            continue
        differences += 1
        print(f"{name}: MISMATCH (oracle {len(oracle)} rows, results {len(sql)} rows)")
        for label, rows in [
            ("only in oracle", set(oracle) - set(sql)),
            ("only in results", set(sql) - set(oracle)),
        ]:
            for row in sorted(rows)[:5]:
                print(f"  {label}: {row}")
    return differences


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
