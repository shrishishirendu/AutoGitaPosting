from __future__ import annotations

import json
from pathlib import Path

from gita_autoposter.core.config import Config
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.db import connect, init_db, load_sequence


def test_skip_missing_verses(tmp_path: Path) -> None:
    dataset_path = tmp_path / "verses.json"
    dataset_path.write_text(
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

    db_path = tmp_path / "app.db"
    config = Config(
        dry_run=True,
        db_path=str(db_path),
        artifact_dir=str(tmp_path / "artifacts"),
        gita_dataset_path=str(dataset_path),
    )

    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, [(1, 3), (1, 1), (1, 2)], reset=True)
        orchestrator = Orchestrator(config, conn)
        report = orchestrator.run_once(run_id="run-skip")

        skipped = conn.execute(
            "SELECT status, error_message FROM verse_history WHERE chapter_number = 1 AND verse_number = 3"
        ).fetchone()

    assert report.status == "success"
    assert skipped is not None
    assert skipped["status"] == "SKIPPED"
    assert "not found" in skipped["error_message"]
