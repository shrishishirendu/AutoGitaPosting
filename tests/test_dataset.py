from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook

from gita_autoposter.agents.verse_fetch import VerseFetchAgent
from gita_autoposter.core.config import Config
from gita_autoposter.core.contracts import SequenceSelection, VerseRef
from gita_autoposter.core.orchestrator import RunContext
from gita_autoposter.dataset_builder import build_verses_json
from gita_autoposter.db import connect, init_db, load_sequence
from gita_autoposter.sequence_loader import read_sequence_xlsx
from gita_autoposter.validation import find_missing_verses


def _write_vendor_json(path: Path) -> None:
    data = [
        {
            "chapter": 1,
            "verse": 1,
            "slok": "धृतराष्ट्र उवाच",
            "translation": "Dhritarashtra said",
        },
        {
            "chapter": 1,
            "verse": 2,
            "slok": "सञ्जय उवाच",
            "translation": "Sanjaya said",
        },
    ]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _write_sequence_xlsx(path: Path, rows: list[tuple[int, int]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["chapter_number", "verse_number"])
    for chapter, verse in rows:
        sheet.append([chapter, verse])
    workbook.save(path)


def test_build_dataset(tmp_path: Path) -> None:
    vendor_dir = tmp_path / "vendor"
    vendor_dir.mkdir()
    vendor_file = vendor_dir / "bhagavad_gita.json"
    _write_vendor_json(vendor_file)

    output_path = tmp_path / "verses.json"
    count = build_verses_json(vendor_dir, output_path)

    assert count == 2
    assert output_path.exists()


def test_verse_fetch_agent_returns_payload(tmp_path: Path) -> None:
    dataset_path = tmp_path / "verses.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "chapter": 1,
                    "verse": 1,
                    "sanskrit": "धृतराष्ट्र उवाच",
                    "translation_en": "Dhritarashtra said",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = RunContext(
            config=Config(gita_dataset_path=str(dataset_path)),
            run_id="run-1",
            db=conn,
            artifact_dir=str(tmp_path / "artifacts"),
        )
        agent = VerseFetchAgent()
        selection = SequenceSelection(verse_ref=VerseRef(chapter=1, verse=1), ord_index=0)
        payload = agent.run(selection, ctx)

    assert payload.sanskrit == "धृतराष्ट्र उवाच"
    assert payload.translation == "Dhritarashtra said"


def test_validate_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "verses.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "chapter": 1,
                    "verse": 1,
                    "sanskrit": "धृतराष्ट्र उवाच",
                    "translation_en": "Dhritarashtra said",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    xlsx_path = tmp_path / "sequence.xlsx"
    _write_sequence_xlsx(xlsx_path, [(1, 1)])
    sequence = read_sequence_xlsx(str(xlsx_path))

    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, sequence, reset=True)
        missing = find_missing_verses(conn, str(dataset_path))

    assert missing == []


def test_validate_dataset_reports_missing(tmp_path: Path) -> None:
    dataset_path = tmp_path / "verses.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "chapter": 1,
                    "verse": 1,
                    "sanskrit": "धृतराष्ट्र उवाच",
                    "translation_en": "Dhritarashtra said",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    xlsx_path = tmp_path / "sequence.xlsx"
    _write_sequence_xlsx(xlsx_path, [(9, 9)])
    sequence = read_sequence_xlsx(str(xlsx_path))

    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        load_sequence(conn, sequence, reset=True)
        missing = find_missing_verses(conn, str(dataset_path))

    assert missing == [(9, 9)]
