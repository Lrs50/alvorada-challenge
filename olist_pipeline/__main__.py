import argparse
import time
import webbrowser

from olist_pipeline.config import DATA, RESULTS, ROOT
from olist_pipeline.db import connect
from olist_pipeline.load import load
from olist_pipeline.migrate import migrate
from olist_pipeline.oracle import QUESTIONS
from olist_pipeline.oracle import main as validate
from olist_pipeline.report import report
from olist_pipeline.run import run

LABELS = {name: label for name, label, *_ in QUESTIONS}


def run_everything(conn):
    started = time.perf_counter()
    run_id, _ = run(conn, DATA)
    for name, result in report(conn).items():
        print(f"Calculated {LABELS[name]}: {len(result['rows']):,} rows", flush=True)
    print("Validating the results against an independent recount...", flush=True)
    if validate():
        print("Validation failed: the results above do not match the recount")
        return 1
    print("Validated all three results against an independent recount: OK")
    dashboard = RESULTS / "dashboard.html"
    print(f"Report generated at {dashboard.relative_to(ROOT).as_posix()} (opening in your browser)")
    webbrowser.open(dashboard.as_uri())
    print(f"Run {run_id} finished in {time.perf_counter() - started:.1f}s")
    return 0


def main():
    parser = argparse.ArgumentParser(prog="olist_pipeline")
    command = parser.add_subparsers(dest="command", required=True)
    for name in ["run", "migrate", "load"]:
        command.add_parser(name)
    args = parser.parse_args()
    with connect() as conn:
        if args.command == "run":
            return run_everything(conn)
        if args.command == "migrate":
            print("applied:", migrate(conn) or "nothing to do")
        else:
            load(conn, DATA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
