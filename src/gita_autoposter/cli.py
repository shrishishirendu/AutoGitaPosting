from __future__ import annotations

import argparse
from pathlib import Path

from gita_autoposter.agents.commentary_agent import CommentaryAgent
from gita_autoposter.core.config import load_config
from gita_autoposter.core.contracts import VersePayload, VerseRef
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.dataset import get_verse
from gita_autoposter.dataset_builder import build_verses_json
from gita_autoposter.db import (
    connect,
    get_last_posted,
    get_recent_caption_rows,
    get_upcoming,
    init_db,
    list_runs,
    load_sequence,
)
from gita_autoposter.sequence_loader import read_sequence_xlsx
from gita_autoposter.validation import find_missing_verses


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


def _build_dataset(args: argparse.Namespace) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    vendor_dir = repo_root / "data" / "vendor" / "gita_gita"
    output_path = repo_root / "data" / "gita" / "verses.json"
    count = build_verses_json(vendor_dir, output_path)
    print(f"Wrote {count} verses to {output_path}")


def _validate_dataset(args: argparse.Namespace) -> None:
    config = load_config()
    with connect(config.db_path) as conn:
        init_db(conn)
        missing = find_missing_verses(conn, config.gita_dataset_path)

    if missing:
        print("Missing verses:")
        for chapter, verse in missing:
            print(f"{chapter}.{verse}")
        raise SystemExit(1)
    print("Dataset validation passed.")


def _preview_commentary(args: argparse.Namespace) -> None:
    config = load_config()
    verse = get_verse(args.chapter, args.verse, config.gita_dataset_path)
    verse_payload = VersePayload(
        verse_ref=VerseRef(chapter=args.chapter, verse=args.verse),
        ord_index=None,
        sanskrit=verse["sanskrit"],
        translation=verse["translation_en"],
    )
    with connect(config.db_path) as conn:
        init_db(conn)
        ctx = type("PreviewCtx", (), {"config": config, "db": conn, "run_id": "preview"})
        agent = CommentaryAgent()
        commentary = agent.run(verse_payload, ctx)

    print("SOCIAL:")
    print(commentary.social_en)
    print("PROFESSIONAL:")
    print(commentary.professional_en)
    print("PRACTICAL:")
    print(commentary.practical_en)
    print("CAPTION:")
    print(commentary.caption_final_en)
    print("HASHTAGS:")
    print(" ".join(commentary.hashtags))


def _list_captions(args: argparse.Namespace) -> None:
    config = load_config()
    with connect(config.db_path) as conn:
        init_db(conn)
        rows = get_recent_caption_rows(conn, args.last)

    for row in rows:
        print(f"{row['created_at']} | {row['fingerprint'] or '-'}")
        print(row["caption_final_en"])
        print("---")


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

    build_cmd = subparsers.add_parser("build-dataset", help="Build the canonical verses dataset.")
    build_cmd.set_defaults(func=_build_dataset)

    validate_cmd = subparsers.add_parser(
        "validate-dataset", help="Validate verse_queue against the verses dataset."
    )
    validate_cmd.set_defaults(func=_validate_dataset)

    preview_cmd = subparsers.add_parser(
        "preview-commentary", help="Generate commentary for a verse."
    )
    preview_cmd.add_argument("--chapter", type=int, required=True)
    preview_cmd.add_argument("--verse", type=int, required=True)
    preview_cmd.set_defaults(func=_preview_commentary)

    list_captions_cmd = subparsers.add_parser(
        "list-captions", help="List recent captions."
    )
    list_captions_cmd.add_argument("--last", type=int, default=5)
    list_captions_cmd.set_defaults(func=_list_captions)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
