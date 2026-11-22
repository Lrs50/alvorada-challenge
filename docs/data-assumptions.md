# Data assumptions

Each row says what the pipeline assumes or does, and how many rows of the real data it affects. Counts come from `core` after a full load of the five CSVs (99,441 orders, 112,650 items, 103,886 payments, 99,441 customers, 32,951 products).

## Cleaning

Every row passed the checks in `sql/transform/`: **0 rows rejected** in all five tables. The checks are still in place because a future file may not be clean. A rejected row goes to `ops.reject` with the reason and its original values.

| Rule | Rows affected |
|---|---|
| Text fields are trimmed, and a blank category becomes `NULL` | 610 products have no category |
| A row is rejected for a blank key, a duplicate key, an unparsable number or date, or a missing parent (customer, order or product) | 0 |
| Timestamps are stored without a time zone (`timestamp`); the source has none | 99,441 orders |
| `core` keeps only the columns the questions need. Dropped: item `seller_id` and `shipping_limit_date`, order approval, carrier and estimated-delivery dates, customer city and zip prefix, product dimensions | all rows |

## Suspicious data that is kept

The pipeline never drops a row for looking odd. These rows stay in `core` so the reconciliation can find them.

| What | Rows | Effect |
|---|---|---|
| Orders with no items: 603 unavailable, 164 canceled, 5 created, 2 invoiced, 1 shipped | 775 | None delivered, so none reach the sales questions. |
| Delivered order with no payment | 1 | Appears in the reconciliation as an order with no payment. |
| Orders whose payment numbers skip or do not start at 1 | 80 | Possible missing payment rows. Kept, and any mismatch shows in the reconciliation. |
| Zero-value payments: 6 vouchers, 3 `not_defined` | 9 | Kept. They add nothing to totals. |
| Payments with 0 installments | 2 | Kept. |
| Canceled orders with a delivery date | 6 | Kept. Only delivered orders count as sales. |
| Delivered orders with no delivery date | 8 | Kept. Sales are placed by purchase date, so they still count. |

## Reconciliation (paid total against items plus freight)

Of the 98,665 orders that have both items and payments:

| Difference | Orders |
|---|---|
| Exactly 0 | 98,089 |
| Up to 0.01 | 273 |
| 0.01 to 0.02 | 36 |
| Over 0.02 | 267 (244 paid more, 23 paid less) |

The divergence rule is an absolute difference over 0.01, so a difference of exactly 0.01 is not flagged. Orders with no payment are flagged separately.

## Decisions

- **Products with no category** are grouped as an explicit `unknown` category in the category ranking, so the ranking total matches total sales. Among delivered orders this is 1,537 of 110,197 items (R$ 170,726.63 of R$ 13,221,498.11, 1.3% of sales).
- **Ranking ties** are broken by category name, ascending, so the top 10 is the same on every run.
- **Reconciliation includes every order status** and never excludes suspicious records.
