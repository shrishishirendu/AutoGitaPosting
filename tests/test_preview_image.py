from __future__ import annotations

import json
import os
from pathlib import Path

from gita_autoposter import cli


def test_preview_image_creates_files(tmp_path: Path) -> None:
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

    os.environ["GITA_DATASET_PATH"] = str(dataset_path)
    os.environ["DB_PATH"] = str(tmp_path / "app.db")
    os.environ["ARTIFACT_DIR"] = str(tmp_path / "artifacts")

    args = type("Args", (), {"chapter": 1, "verse": 1})
    cli._preview_image(args)

    raw_dir = tmp_path / "artifacts" / "images" / "raw"
    composed_dir = tmp_path / "artifacts" / "images" / "composed"
    assert any(raw_dir.iterdir())
    assert any(composed_dir.iterdir())
