from pathlib import Path

from gita_autoposter.core.config import Config
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.db import connect, init_db, load_sequence


def test_db_records(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    artifact_dir = tmp_path / "artifacts"
    dataset_path = tmp_path / "verses.json"
    dataset_path.write_text(
        """[
  {
    "chapter_number": 1,
    "verse_number": 1,
    "sanskrit": "धृतराष्ट्र उवाच",
    "english_translation": "Dhritarashtra said"
  },
  {
    "chapter_number": 1,
    "verse_number": 2,
    "sanskrit": "सञ्जय उवाच",
    "english_translation": "Sanjaya said"
  }
]""",
        encoding="utf-8",
    )
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
        orchestrator.run_once(run_id="run-db-test")

        run_row = conn.execute("SELECT * FROM runs WHERE run_id = ?", ("run-db-test",)).fetchone()
        draft_row = conn.execute("SELECT * FROM drafts WHERE run_id = ?", ("run-db-test",)).fetchone()

    assert run_row is not None
    assert run_row["status"] == "success"
    assert draft_row is not None
    assert draft_row["status"] in ("success", "posted")
