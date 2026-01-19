from __future__ import annotations

import json
from pathlib import Path

from gita_autoposter.dataset import load_dataset
from gita_autoposter.db import get_queue_pairs


def validate_dataset_file(dataset_path: str) -> tuple[list[str], list[str]]:
    path = Path(dataset_path)
    if not path.exists():
        return [], [f"Dataset not found: {path}"]

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        return [], ["Dataset must be a JSON list of verse records."]

    warnings: list[str] = []
    errors: list[str] = []
    seen: set[tuple[int, int]] = set()
    chapters_present: set[int] = set()
    has_devanagari = False

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errors.append(f"Record {index} is not an object.")
            continue
        chapter_value = item.get("chapter_number")
        verse_value = item.get("verse_number")
        if chapter_value is None or verse_value is None:
            errors.append(f"Record {index} missing chapter_number or verse_number.")
            continue
        try:
            chapter = int(chapter_value)
            verse = int(verse_value)
        except (TypeError, ValueError):
            errors.append(f"Record {index} has invalid chapter_number or verse_number.")
            continue
        key = (chapter, verse)
        if key in seen:
            errors.append(f"Duplicate verse detected at {chapter}.{verse}.")
        else:
            seen.add(key)
        chapters_present.add(chapter)
        sanskrit = str(item.get("sanskrit", ""))
        if not has_devanagari and any(0x0900 <= ord(ch) <= 0x097F for ch in sanskrit):
            has_devanagari = True

    total = len(data)
    if total < 100:
        errors.append(f"Dataset has only {total} verses (expected >= 100).")
    elif total < 650:
        warnings.append(f"Dataset has only {total} verses (expected >= 650).")

    missing_chapters = [c for c in range(1, 19) if c not in chapters_present]
    if missing_chapters:
        warnings.append(
            "Dataset missing chapters: " + ", ".join(str(c) for c in missing_chapters)
        )

    if not has_devanagari:
        errors.append("Dataset sanskrit field lacks Devanagari characters.")

    return warnings, errors


def find_missing_verses(conn, dataset_path: str) -> list[tuple[int, int]]:
    dataset = load_dataset(dataset_path)
    missing: list[tuple[int, int]] = []
    for chapter, verse, _ord_index in get_queue_pairs(conn):
        if (chapter, verse) not in dataset:
            missing.append((chapter, verse))
    return missing
