from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    dry_run: bool = True
    db_path: str = "data/app.db"
    artifact_dir: str = "artifacts"
    sequence_xlsx_path: str = "data/sequence/verses.xlsx"
    gita_dataset_path: str = "data/gita/verses.json"


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    load_dotenv()
    dry_run = _parse_bool(os.getenv("DRY_RUN"), True)
    db_path = os.getenv("DB_PATH", "data/app.db")
    artifact_dir = os.getenv("ARTIFACT_DIR", "artifacts")
    sequence_xlsx_path = os.getenv("SEQUENCE_XLSX_PATH", "data/sequence/verses.xlsx")
    gita_dataset_path = os.getenv("GITA_DATASET_PATH", "data/gita/verses.json")
    return Config(
        dry_run=dry_run,
        db_path=db_path,
        artifact_dir=artifact_dir,
        sequence_xlsx_path=sequence_xlsx_path,
        gita_dataset_path=gita_dataset_path,
    )
