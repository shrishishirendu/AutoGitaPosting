from pathlib import Path

from openpyxl import Workbook

from gita_autoposter.agents.sequence import SequenceAgent
from gita_autoposter.core.config import Config
from gita_autoposter.core.contracts import SequenceInput
from gita_autoposter.core.orchestrator import RunContext
from gita_autoposter.db import (
    connect,
    get_sequence_snapshot,
    init_db,
    load_sequence,
    mark_verse_posted,
)
from gita_autoposter.sequence_loader import read_sequence_xlsx


def _write_sequence_xlsx(path: Path, rows: list[tuple[int, int]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["chapter_number", "verse_number"])
    for chapter, verse in rows:
        sheet.append([chapter, verse])
    workbook.save(path)


def test_load_sequence_from_xlsx(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "verses.xlsx"
    rows = [(1, 1), (1, 2), (2, 1)]
    _write_sequence_xlsx(xlsx_path, rows)

    sequence = read_sequence_xlsx(str(xlsx_path))

    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, sequence, reset=True)
        snapshot = get_sequence_snapshot(conn)

    assert snapshot == [(1, 1, 0), (1, 2, 1), (2, 1, 2)]


def test_sequence_reserve_and_advance(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, [(1, 1), (1, 2)], reset=True)
        agent = SequenceAgent()
        ctx = RunContext(
            config=Config(),
            run_id="run-1",
            db=conn,
            artifact_dir=str(tmp_path / "artifacts"),
        )

        first = agent.run(SequenceInput(run_id="run-1"), ctx)
        mark_verse_posted(conn, "run-1")
        second = agent.run(SequenceInput(run_id="run-2"), ctx)

    assert first.ord_index == 0
    assert second.ord_index == 1


def test_sequence_replay_reserved_on_crash(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, [(1, 1), (1, 2)], reset=True)
        agent = SequenceAgent()
        ctx = RunContext(
            config=Config(),
            run_id="run-1",
            db=conn,
            artifact_dir=str(tmp_path / "artifacts"),
        )

        first = agent.run(SequenceInput(run_id="run-1"), ctx)
        replay = agent.run(SequenceInput(run_id="run-2"), ctx)
        mark_verse_posted(conn, "run-2")
        advanced = agent.run(SequenceInput(run_id="run-3"), ctx)

    assert first.ord_index == 0
    assert replay.ord_index == 0
    assert advanced.ord_index == 1
