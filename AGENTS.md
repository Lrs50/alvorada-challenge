# AGENTS.md

Sales pipeline: loads Olist CSVs into PostgreSQL; SQL answers sales, category-ranking and payment-reconciliation questions. Reruns must not duplicate rows or change totals.

## Commands

- First time: copy `.env.example` to `.env` (the one source of config; `make` loads it). Run `migrate` and `test` through `make`, not bare `uv run`, so `DATABASE_URL` is set.
- `make setup` install env (`uv sync`); `make lint` ruff check + format check.
- `make migrate` apply `sql/migrations/*.sql` (numbered, append-only: never edit an applied file).
- `make load` replace the `raw` tables with the CSVs in `data/` (one transaction; run `make migrate` first).
- `make run` start Postgres, then migrate, load, transform and log the run in `ops.pipeline_runs`.
- `make report` run the question queries in `sql/queries/` and write `results/*.csv` and `results/dashboard.html` (run `make run` first).
- `make test` start Postgres, then run pytest.
- `make up` / `make down` start / stop Postgres (Docker).
- Use `uv` for everything; never `pip`. Add new targets here when they exist.

## Rules

- Smallest change that works. No abstraction without two call sites; no option, helper, file or dependency "for later". Ask before adding a dependency.
- Business logic lives in SQL. Python only orchestrates.
- Pipeline SQL (migrations, load, questions) lives in `.sql` files: migrations are scripts, queries are one per file. Tiny plumbing queries (migration runner bootstrap, test setup and schema assertions) may stay as constants beside the code that uses them. No comments at the top of Python files.
- Tests first. Expected values are hand-calculated, never copied from code output. Fictional fixtures only.
- Document each data assumption, with the number of rows it affects, in docs/.
- `make lint` and tests pass before handing work over.

## Git

- Never commit. When asked, reply with one conventional-commit line (imperative, <=72 chars) and nothing else.
- One concern per commit; a query change and its regenerated results go together.
- Only README.md mentions the exercise; elsewhere write as a normal project.

## Working with the human

- Propose before touching more than one or two files. Small diffs; stop for review.
- State assumptions. Say what was verified and how; report failures with real output.
- No unrequested refactors or docs.
