# AGENTS.md

Sales pipeline: loads Olist CSVs into PostgreSQL; SQL answers sales, category-ranking and payment-reconciliation questions. Reruns must not duplicate rows or change totals.

## Commands

- `make setup` install env (`uv sync`); `make lint` ruff check + format check.
- Use `uv` for everything; never `pip`. Add new targets here when they exist.

## Rules

- Smallest change that works. No abstraction without two call sites; no option, helper, file or dependency "for later". Ask before adding a dependency.
- Business logic lives in SQL (one query per file). Python only orchestrates.
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
