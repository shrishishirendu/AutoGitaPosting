from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from gita_autoposter import cli
from gita_autoposter.core.config import Config
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.db import (
    connect,
    finish_run,
    init_db,
    insert_run,
    load_sequence,
    update_run_stage,
)


def _write_dataset(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "chapter_number": 1,
                    "verse_number": 1,
                    "sanskrit": "धृतराष्ट्र उवाच",
                    "english_translation": "Dhritarashtra said",
                },
                {
                    "chapter_number": 1,
                    "verse_number": 2,
                    "sanskrit": "सञ्जय उवाच",
                    "english_translation": "Sanjaya said",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_run_once_writes_report_and_log(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    artifact_dir = tmp_path / "artifacts"
    dataset_path = tmp_path / "verses.json"
    _write_dataset(dataset_path)
    config = Config(
        dry_run=True,
        db_path=str(db_path),
        artifact_dir=str(artifact_dir),
        gita_dataset_path=str(dataset_path),
    )

    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, [(1, 1), (1, 2)], reset=True)
        orchestrator = Orchestrator(config, conn)
        report = orchestrator.run_once(run_id="run-obs")

    run_dir = artifact_dir / "run-obs"
    report_path = run_dir / "run_report.json"
    log_path = run_dir / "run.log"

    assert report.status == "success"
    assert report_path.exists()
    assert log_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-obs"
    assert payload["status"] == "success"
    assert payload["output_paths"]["caption"] is not None


def test_failed_run_persists_stage_and_report(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    artifact_dir = tmp_path / "artifacts"
    missing_dataset = tmp_path / "missing.json"
    config = Config(
        dry_run=True,
        db_path=str(db_path),
        artifact_dir=str(artifact_dir),
        gita_dataset_path=str(missing_dataset),
    )

    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, [(1, 1)], reset=True)
        orchestrator = Orchestrator(config, conn)
        with pytest.raises(Exception):
            orchestrator.run_once(run_id="run-fail")

        run_row = conn.execute(
            "SELECT status, stage, error_message FROM runs WHERE run_id = ?",
            ("run-fail",),
        ).fetchone()

    assert run_row is not None
    assert run_row["status"] == "failed"
    assert run_row["stage"] == "fetch"
    assert run_row["error_message"]

    report_path = artifact_dir / "run-fail" / "run_report.json"
    assert report_path.exists()


def test_status_json_outputs_valid_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "app.db"
    os.environ["DB_PATH"] = str(db_path)

    with connect(str(db_path)) as conn:
        init_db(conn)
        insert_run(conn, "run-json", "running", datetime.utcnow(), stage="init")
        update_run_stage(conn, "run-json", "finish")
        finish_run(conn, "run-json", "success", None, None)

    args = type("Args", (), {"limit": 5, "last": False, "json": True})
    cli._status(args)
    output = capsys.readouterr().out.strip()
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["run_id"] == "run-json"


def test_debug_last_shows_failed_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "app.db"
    os.environ["DB_PATH"] = str(db_path)
    os.environ["ARTIFACT_DIR"] = str(tmp_path / "artifacts")

    with connect(str(db_path)) as conn:
        init_db(conn)
        insert_run(conn, "run-failed", "running", datetime.utcnow(), stage="fetch")
        finish_run(conn, "run-failed", "failed", None, "boom")

    args = type("Args", (), {})
    cli._debug_last(args)
    output = capsys.readouterr().out
    assert "run-failed" in output
