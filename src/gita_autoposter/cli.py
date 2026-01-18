from __future__ import annotations

import argparse
from pathlib import Path

from gita_autoposter.core.config import load_config
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.db import (
    connect,
    get_last_posted,
    get_upcoming,
    init_db,
    list_runs,
    load_sequence,
)
from gita_autoposter.sequence_loader import read_sequence_xlsx


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


def _load_sequence(args: argparse.Namespace) -> None:
    config = load_config()
    sequence = read_sequence_xlsx(config.sequence_xlsx_path)
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(config.db_path) as conn:
        init_db(conn)
        outcome = load_sequence(conn, sequence, args.reset)
    if outcome == "unchanged":
        print("Sequence already up to date.")
    else:
        print("Sequence loaded.")


def _show_sequence(args: argparse.Namespace) -> None:
    config = load_config()
    with connect(config.db_path) as conn:
        init_db(conn)
        upcoming = get_upcoming(conn, args.limit)
        posted = get_last_posted(conn, args.limit)

    print("Upcoming:")
    for chapter, verse, ord_index in upcoming:
        print(f"{ord_index}: {chapter}.{verse}")

    print("Last posted:")
    for chapter, verse, ord_index, posted_at in posted:
        print(f"{ord_index}: {chapter}.{verse} at {posted_at}")


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

    load_cmd = subparsers.add_parser("load-sequence", help="Load verse sequence from Excel.")
    load_cmd.add_argument("--reset", action="store_true", help="Wipe and reload sequence.")
    load_cmd.set_defaults(func=_load_sequence)

    show_cmd = subparsers.add_parser("show-sequence", help="Show upcoming and posted verses.")
    show_cmd.add_argument("--limit", type=int, default=5, help="Number of verses to show.")
    show_cmd.set_defaults(func=_show_sequence)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
