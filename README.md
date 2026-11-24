# Olist sales pipeline

An ELT pipeline for the Olist e-commerce data. Docker runs PostgreSQL 16 and uv manages the Python environment. The pipeline loads five CSV files as text into a `raw` schema, rebuilds typed tables with primary and foreign keys in `core`, and logs every run and every rejected row in `ops`. The transformations and the three business questions are written in SQL, and Python only runs them. The answers are written to CSV files and an HTML dashboard, then checked against an independent pandas recount, and 30 tests cover the edge cases. Running it again on the same files does not duplicate rows or change totals.

|            |                                                    |
| ---------- | -------------------------------------------------- |
| Case       | Caso 10, sales pipeline and payment reconciliation |
| Focus      | Correct results, and how I checked them            |
| Time spent | About 4 hours                                      |
| Video      | _link to be added_                               |

## Quick start

You need [Docker](https://docs.docker.com/get-started/get-docker/) and [uv](https://docs.astral.sh/uv/getting-started/installation/). [make](https://www.gnu.org/software/make/) is optional.

```
cp .env.example .env
make run
make test
```

`make run` starts Postgres, applies the migrations, loads the CSVs, builds the typed tables, writes the results, recounts all three answers independently with pandas and opens the dashboard in your browser if the machine has one. It takes about 15 seconds and exits with code 1 if the recount disagrees. Docker starts PostgreSQL 16 on port 5432, so that port must be free.

Without make:

```
docker compose up -d --wait
uv run --env-file .env python -m olist_pipeline run
uv run --env-file .env pytest
```

## Data

The five CSVs come from the [Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (the license is on that page). They are committed in `data/`, 48 MB in total, so the project runs without a Kaggle account. In a real project raw files would live in object storage, not in Git. To use other copies, put files with these names in `data/`:

- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_products_dataset.csv`

## Results and querying

### Outputs

The answers are in `results/`. The SQL for each is in `sql/queries/`.

- `q1_sales_by_month_state.csv` (556 rows)
- `q2_top_categories_by_month.csv` (212 rows)
- `q3_payment_divergences.csv` (1,076 rows)
- `dashboard.html`

Headline figures:

- Delivered sales: R$ 13,221,498.11 over 96,478 orders.
- Q3 flags 1,076 orders: 772 `no items`, 264 `paid more`, 39 `paid less` and 1 `no payment`. The first 206 rows of the Q3 file are `no items` orders, which have the largest differences.

### Querying the database

```
docker compose exec db psql -U olist -d olist
```

- `core`: typed tables with primary and foreign keys.
- `ops.pipeline_runs`: one row per run (status, rows read, loaded and rejected, error text on failure).
- `ops.reject`: rejected rows with their reason and original values.

```sql
select run_id, status, rows_read, rows_loaded, rows_rejected from ops.pipeline_runs;
```

## How it works

Data moves through three schemas:

- `raw`: the files as text plus a load time. Replaced in one transaction.
- `core`: typed rows rebuilt from `raw` in a second transaction.
- `ops`: the run log and the rejected rows.

If the transform fails, `core` keeps the previous run's data while `raw` holds the new files, the failure is logged with its error and the command exits non-zero. A rerun starts from a clean replace of both, which is why it is safe.

The logic is in SQL and Python only runs it:

- `sql/migrations`: creates the tables.
- `sql/transform`: moves raw to core and rejects bad rows.
- `sql/queries`: one file per question.
- `olist_pipeline/`: runs those files and writes the results.
- `olist_pipeline/oracle.py`: recomputes the three answers from the CSVs with pandas and shares no code with the pipeline. It assumes clean input, as the Olist files are.

## Tests

`make test` runs 30 tests on a throwaway database with fictional fixtures. Expected values are calculated by hand. Three worth reading:

| Test                                                                               | Expected                                                                                        | Mistake it catches                                                |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Order with several items and payments (`test_q3` order m1, `test_q1` order o1) | m1 is billed 35.00 and paid 35.00, so it is not flagged. o1 counts once in its month and state. | Joining items to payments multiplies rows and doubles the totals. |
| One-cent boundary (`test_q3`, m2 and m9 against m3 and m10)                      | A difference of +0.01 or -0.01 is not flagged. A difference of 0.02 is.                         | A wrong comparison operator, or rounding errors from floats.      |
| Rerun (`test_worked_example`, `test_run`)                                      | Same answers and same row counts, plus a new row in `ops.pipeline_runs`.                      | Rows duplicated by a second load.                                 |

`test_worked_example.py` also runs the brief's A, B and C orders through the whole pipeline twice. `test_pipeline.py` checks that a wrong result fails the recount and names the question.

## Data quality and assumptions

Every row passed the checks, so 0 rows were rejected. The checks stay in place for future files. The exploration behind these numbers is in `notebooks/data_analysis.ipynb`. What the data does contain:

- 775 orders have no items, none of them delivered. All 775 have payment rows. 772 paid more than 0 and appear in Q3 as `no items`; the other 3 are canceled orders with a single 0.00 payment and are not flagged.
- 1 delivered order has no payment.
- 80 orders have payment sequence numbers that skip or do not start at 1.
- 610 products have no category.
- 303 orders differ from their billed total by more than 0.01. 249 of the 264 overpaid orders were paid in installments, which fits interest, but the data has no interest field so I could not confirm it.

Assumptions:

- A product with no category is ranked as `unknown`.
- Ranking ties are broken by category name. Neither choice changes any of the 212 rows here.
- Q3 checks every status, and "no payment" means no payment rows. A single payment of 0.00 is compared like any other.
- Sales are placed by purchase date, so an order bought on 31 January and delivered in February counts in January.
- Money is `NUMERIC(12, 2)`, so the 0.01 limit is exact.

Each rule with its row count is in [docs/data-assumptions.md](docs/data-assumptions.md).

## Decisions

**Keeping the raw layer.** The AI suggested loading straight into typed tables and dropping `raw` to keep the project smaller. I wanted to know what that would cost. Without `raw`, a row that fails typing has nowhere to be inspected, and fixing a transform means rereading the files. With it, a rejected row keeps its original text (the dirty fixture stores the price `abc` in `ops.reject`) and the transform can be rerun from the database. I kept `raw` and accepted the extra copy of the data.

**The 80 payment gaps.** Orders whose payment numbers skip a value could be missing a payment row, which would explain underpaid orders. I compared the 80 orders against the 303 mismatches. 79 of them reconcile within 0.01, the other is flagged only for having no items, and none of the 303 has a gap. The gaps do not explain the mismatches, so I kept the rows and documented them.

## Use of AI

I looked at the CSVs myself first, then proposed the architecture for the whole problem: uv for the environment, Docker for Postgres, the file layout, the migrations and the `raw`, `core` and `ops` schemas, with the logic in SQL. I discussed it with Claude to check it against good practice. The suggestion to drop `raw` came up in that discussion.

Before any code was written I wrote `AGENTS.md`: business logic in SQL, smallest change that works, hand-calculated test expectations, fictional fixtures only, and no commits by the agent. It also says lint and tests must pass before work is handed over. Claude Code then wrote the code inside those rules (migrations, runner, fixtures, report), and I used it as an implementation tool.

I reviewed what it produced and pushed back on complexity: repeated code, internal names in the terminal output, a report path tied to one machine, and separate `report` and `audit` targets that `make run` makes unnecessary. When I reviewed the queries I tested two changes against the data. Totaling items per order before joining in Q1 made the query faster, so I kept it (about 520 ms before and 300 ms after on 112,000 items). A zero-division guard and an extra `no items or payment` label in Q3 would never trigger here, so I left them out. The results were verified with the hand-calculated tests, the A, B and C example, and the pandas recount.

## Implemented and proposed

Implemented and validated: reruns that keep the same counts and results, rollback with a logged failure, the run log, the three answers against the recount, and the 30 tests.

Proposed, not built:

- **Volume.** The only measurement is Q1 on 112,000 items. Larger loads would likely need an index on `orders(customer_id)`, partitioning by month or a monthly summary table. I tried none of these.
- **Updates.** Each run reloads everything. That fits files that are complete snapshots, because an upsert would keep rows that disappeared from the source and change the totals. If the source sent only changes, `raw` would keep each batch and `core` would upsert on the natural keys (`order_id`, `(order_id, order_item_id)` and `(order_id, payment_sequential)`), with an explicit rule for removed rows. I did not build this.
- **New sources.** A new file needs a `raw` table, a transform file and an entry in `TABLES`. I have not tried it with a sixth source.
- **Failure recovery.** A process killed hard leaves its run marked `running`. Migrations have no checksum, nothing stops two runs at once, and the recount result is not stored in `ops.pipeline_runs`.
- **CI.** Lint and tests are run by hand with `make lint` and `make test`.
