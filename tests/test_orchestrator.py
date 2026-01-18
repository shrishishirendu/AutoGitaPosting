from pathlib import Path

from gita_autoposter.core.config import Config
from gita_autoposter.core.orchestrator import Orchestrator
from gita_autoposter.db import connect, init_db, load_sequence


def test_orchestrator_dry_run(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    artifact_dir = tmp_path / "artifacts"
    config = Config(dry_run=True, db_path=str(db_path), artifact_dir=str(artifact_dir))

    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, [(1, 1), (1, 2)], reset=True)
        orchestrator = Orchestrator(config, conn)
        report = orchestrator.run_once(run_id="run-test")

    assert report.status == "success"
    composed_image = artifact_dir / "images" / "composed" / "run-test_composed.png"
    assert composed_image.exists()
