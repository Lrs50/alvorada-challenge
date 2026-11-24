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
| Orders with no items: 603 unavailable, 164 canceled, 5 created, 2 invoiced, 1 shipped | 775 | None delivered, so none reach the sales questions. All 775 have payment rows. 772 paid more than 0 and appear in the reconciliation as `no items`; 3 canceled orders have a single 0.00 payment and are not flagged. |
| Delivered order with no payment | 1 | Appears in the reconciliation as `no payment`. |
| Orders whose payment numbers skip or do not start at 1 | 80 | Kept. 79 of them still reconcile within 0.01, and 1 is flagged for having no items. None of the 303 amount mismatches has a gap, so the gaps do not explain the mismatches. |
| Zero-value payments: 6 vouchers, 3 `not_defined`, on 8 orders | 9 | Kept. They add nothing to totals, and none of the 8 orders is flagged. |
| Payments with 0 installments | 2 | Kept. |
| Canceled orders with a delivery date | 6 | Kept. Only delivered orders count as sales. |
| Delivered orders with no delivery date | 8 | Kept. Sales are placed by purchase date, so they still count. |

## Reconciliation (paid total against items plus freight)

Of the 98,665 orders that have both items and payments:

| Difference | Orders |
|---|---|
| Exactly 0 | 98,089 |
| Over 0 up to 0.01 (not flagged) | 273 |
| Over 0.01 up to 0.02 | 36 |
| Over 0.02 | 267 (244 paid more, 23 paid less) |

The divergence rule is an absolute difference over 0.01, so a difference of exactly 0.01 is not flagged (273 orders).

### What the payment divergences query flags

Billed is items plus freight, and the difference is paid minus billed. An order is flagged when it has no payment rows, or when the absolute difference is over 0.01. Every order status is checked. A missing side counts as 0 in the comparison. Items and payments are totaled per order before they are compared, so an order with several items and several payments is not multiplied.

| Reason | Orders | Meaning |
|---|---|---|
| `no items` | 772 | The order has payments but no items, so billed is 0. |
| `paid more` | 264 | Paid exceeds billed by more than 0.01. |
| `paid less` | 39 | Billed exceeds paid by more than 0.01. |
| `no payment` | 1 | The order has items and no payment rows. |
| **Total** | **1,076** | |

By status: 603 unavailable, 300 delivered, 163 canceled, 5 created, 3 shipped, 2 invoiced. The largest difference is R$ 3,782.19, a `no items` order, so the top of the result file is all `no items`; the 303 `paid more` and `paid less` orders are the pricing mismatches.

The overpayments are consistent with installment interest: 249 of the 264 `paid more` orders were paid in installments. The data has no interest field, so this is not verified. Among the 39 `paid less` orders, 20 used installments.

The 3 canceled orders whose only payment is 0.00 and which have no items are not flagged: nothing was paid and nothing was billed.

## Decisions

- **Products with no category** are grouped as an explicit `unknown` category in the category ranking, so the ranking total matches total sales. Among delivered orders this is 1,537 of 110,197 items (R$ 170,726.63 of R$ 13,221,498.11, 1.3% of sales). On this data `unknown` never reaches the top 10 of any month, so it changes none of the 212 result rows. It matters only if a future file has more uncategorized sales.
- **Ranking ties** are broken by category name, ascending, so the top 10 is the same on every run. No month has a tie between the 10th and 11th category here, so this also changes none of the 212 rows. It is covered by a test.
- **Reconciliation includes every order status** and never excludes suspicious records. Orders with items but no payments, and payments but no items, are both flagged with their own reason.
- **"No payment" means no payment rows.** An order whose only payment is 0.00 is not reported as "no payment": it is compared like any other, and 3 canceled orders with no items match at 0 against 0. An order with neither items nor payment rows would be flagged as `no payment` (0 cases here).
- **Money is exact.** Prices, freight and payments are `NUMERIC(12, 2)`, so the 0.01 boundary is compared without floating-point drift. `avg_ticket` is rounded to two decimals.
