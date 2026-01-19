from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple


class VerseNotFoundError(KeyError):
    pass


_DATASET_CACHE: Dict[str, Dict[Tuple[int, int], dict]] = {}


def load_dataset(path: str) -> Dict[Tuple[int, int], dict]:
    if path in _DATASET_CACHE:
        return _DATASET_CACHE[path]

    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with dataset_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON list of verse records.")

    index: Dict[Tuple[int, int], dict] = {}
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Dataset contains a non-object record.")
        chapter_value = item.get("chapter_number", item.get("chapter"))
        verse_value = item.get("verse_number", item.get("verse"))
        if chapter_value is None or verse_value is None:
            raise ValueError("Dataset record missing chapter or verse number.")
        chapter = int(chapter_value)
        verse = int(verse_value)
        sanskrit = str(item.get("sanskrit", "")).strip()
        translation = str(
            item.get("english_translation", item.get("translation_en", ""))
        ).strip()
        if not sanskrit or not translation:
            raise ValueError(f"Missing required text for {chapter}.{verse}.")
        item.setdefault("chapter_number", chapter)
        item.setdefault("verse_number", verse)
        item.setdefault("english_translation", translation)
        index[(chapter, verse)] = item

    _DATASET_CACHE[path] = index
    return index


def get_verse(chapter: int, verse: int, path: str) -> dict:
    index = load_dataset(path)
    key = (chapter, verse)
    if key not in index:
        raise VerseNotFoundError(f"Verse not found in dataset: {chapter}.{verse}")
    return index[key]
