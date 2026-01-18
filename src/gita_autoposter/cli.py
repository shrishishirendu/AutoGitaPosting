from __future__ import annotations

import argparse
from pathlib import Path

from gita_autoposter.core.config import load_config
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.db import connect, init_db, list_runs


def _init_db(args: argparse.Namespace) -> None:
    config = load_config()
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(config.db_path) as conn:
        init_db(conn)
    print(f"Initialized database at {config.db_path}")


def _run_once(args: argparse.Namespace) -> None:
    config = load_config()
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(config.db_path) as conn:
        orchestrator = Orchestrator(config, conn)
        report = orchestrator.run_once()
    print(f"Run {report.run_id} finished with status {report.status}")


def _status(args: argparse.Namespace) -> None:
    config = load_config()
    with connect(config.db_path) as conn:
        rows = list_runs(conn, args.limit)
    for row in rows:
        print(
            f"{row['run_id']} | {row['status']} | {row['started_at']} | "
            f"{row['finished_at'] or '-'}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gita-autoposter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init-db", help="Initialize the SQLite database.")
    init_cmd.set_defaults(func=_init_db)

    run_cmd = subparsers.add_parser("run-once", help="Run the agent pipeline once.")
    run_cmd.set_defaults(func=_run_once)

    status_cmd = subparsers.add_parser("status", help="Show recent runs.")
    status_cmd.add_argument("--limit", type=int, default=5, help="Number of runs to show.")
    status_cmd.set_defaults(func=_status)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
