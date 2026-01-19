from __future__ import annotations

import argparse
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from gita_autoposter.agents.commentary_agent import CommentaryAgent
from gita_autoposter.agents.image_compose import ImageComposeAgent
from gita_autoposter.agents.image_generate import ImageGenerateAgent
from gita_autoposter.agents.image_prompt import ImagePromptAgent
from gita_autoposter.agents.scheduler import SchedulerAgent
from gita_autoposter.core.config import load_config
from gita_autoposter.core.contracts import ImageComposeInput, ImagePromptInput, VersePayload, VerseRef
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.core.visual_intent import resolve_visual_intent
from gita_autoposter.dataset import get_verse
from gita_autoposter.dataset_builder import build_verses_json
from gita_autoposter.db import (
    connect,
    get_last_posted,
    get_recent_caption_rows,
    get_recent_image_rows,
    get_upcoming,
    init_db,
    list_runs,
    load_sequence,
)
from gita_autoposter.sequence_loader import read_sequence_xlsx
from gita_autoposter.validation import validate_dataset_file


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
    csv_path = repo_root / "data" / "gita" / "raw" / "main_utf8.csv"
    output_path = repo_root / "data" / "gita" / "verses.json"
    count = build_verses_json(csv_path, output_path)
    print(f"Wrote {count} verses to {output_path}")


def _validate_dataset(args: argparse.Namespace) -> None:
    config = load_config()
    warnings, errors = validate_dataset_file(config.gita_dataset_path)
    for warning in warnings:
        print(f"Warning: {warning}")
    if errors:
        print("Dataset validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("Dataset validation passed.")


def _preview_commentary(args: argparse.Namespace) -> None:
    config = load_config()
    verse = get_verse(args.chapter, args.verse, config.gita_dataset_path)
    verse_payload = VersePayload(
        verse_ref=VerseRef(chapter=args.chapter, verse=args.verse),
        ord_index=None,
        sanskrit=verse["sanskrit"],
        translation=verse["english_translation"],
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


def _schedule_once(args: argparse.Namespace) -> None:
    config = load_config()
    scheduler = SchedulerAgent(config.timezone, config.post_time)
    scheduled = scheduler.next_scheduled_time().scheduled_time
    scheduled_str = scheduled.isoformat()
    with connect(config.db_path) as conn:
        init_db(conn)
        orchestrator = Orchestrator(config, conn)
        report = orchestrator.run_once(post_now=False, scheduled_time=scheduled_str)
    print(f"Scheduled run {report.run_id} for {scheduled_str}")


def _post_now(args: argparse.Namespace) -> None:
    config = load_config()
    timezone = ZoneInfo(config.timezone)
    scheduled_str = datetime.now(timezone).isoformat()
    with connect(config.db_path) as conn:
        init_db(conn)
        orchestrator = Orchestrator(config, conn)
        report = orchestrator.run_once(post_now=True, scheduled_time=scheduled_str)
    print(f"Run {report.run_id} finished with status {report.status}")


def _run_scheduler(args: argparse.Namespace) -> None:
    config = load_config()
    scheduler = SchedulerAgent(config.timezone, config.post_time)
    while True:
        next_time = scheduler.next_scheduled_time().scheduled_time
        wait_seconds = max(0, (next_time - datetime.now(next_time.tzinfo)).total_seconds())
        print(f"Next run at {next_time.isoformat()} ({int(wait_seconds)}s)")
        time.sleep(wait_seconds)
        with connect(config.db_path) as conn:
            init_db(conn)
            orchestrator = Orchestrator(config, conn)
            orchestrator.run_once(post_now=True, scheduled_time=next_time.isoformat())


def _preview_image(args: argparse.Namespace) -> None:
    config = load_config()
    verse = get_verse(args.chapter, args.verse, config.gita_dataset_path)
    verse_payload = VersePayload(
        verse_ref=VerseRef(chapter=args.chapter, verse=args.verse),
        ord_index=None,
        sanskrit=verse["sanskrit"],
        translation=verse["english_translation"],
    )
    with connect(config.db_path) as conn:
        init_db(conn)
        ctx = type(
            "PreviewCtx",
            (),
            {"config": config, "db": conn, "run_id": "preview-image", "artifact_dir": config.artifact_dir},
        )
        commentary = CommentaryAgent().run(verse_payload, ctx)
        visual_intent = resolve_visual_intent(verse_payload, commentary)
        prompt_input = ImagePromptInput(
            verse_payload=verse_payload,
            commentary=commentary,
            visual_intent=visual_intent,
        )
        prompt = ImagePromptAgent().run(prompt_input, ctx)
        raw = ImageGenerateAgent().run(prompt, ctx)
        composed = ImageComposeAgent().run(ImageComposeInput(verse_payload=verse_payload, image=raw), ctx)

    print(
        f"VisualIntent: {visual_intent.intent_type} "
        f"(confidence={visual_intent.confidence}) {visual_intent.rationale}"
    )
    print(f"Prompt: {prompt.prompt_text}")
    print(f"Raw image: {raw.path_raw}")
    print(f"Composed image: {composed.path_composed}")


def _list_images(args: argparse.Namespace) -> None:
    config = load_config()
    with connect(config.db_path) as conn:
        init_db(conn)
        rows = get_recent_image_rows(conn, args.last)

    for row in rows:
        print(
            f"{row['created_at']} | {row['prompt_fingerprint'] or '-'} | "
            f"raw={row['hash_raw'] or '-'} composed={row['hash_composed'] or '-'}"
        )
        if row["prompt_text"]:
            print(row["prompt_text"])
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
        "validate-dataset", help="Validate the verses dataset."
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

    preview_image_cmd = subparsers.add_parser(
        "preview-image", help="Generate prompt, raw, and composed images."
    )
    preview_image_cmd.add_argument("--chapter", type=int, required=True)
    preview_image_cmd.add_argument("--verse", type=int, required=True)
    preview_image_cmd.set_defaults(func=_preview_image)

    list_images_cmd = subparsers.add_parser(
        "list-images", help="List recent image prompts and hashes."
    )
    list_images_cmd.add_argument("--last", type=int, default=5)
    list_images_cmd.set_defaults(func=_list_images)

    schedule_cmd = subparsers.add_parser(
        "schedule-once", help="Schedule a run for the next post time."
    )
    schedule_cmd.set_defaults(func=_schedule_once)

    post_now_cmd = subparsers.add_parser(
        "post-now", help="Run the pipeline immediately."
    )
    post_now_cmd.set_defaults(func=_post_now)

    scheduler_cmd = subparsers.add_parser(
        "run-scheduler", help="Run the scheduler loop."
    )
    scheduler_cmd.set_defaults(func=_run_scheduler)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
