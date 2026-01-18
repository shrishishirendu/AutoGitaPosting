from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def _first_value(item: dict, keys: Iterable[str]) -> Any:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return None


def _find_vendor_json(vendor_dir: Path) -> Path:
    candidates = [
        "bhagavad_gita.json",
        "gita.json",
        "verses.json",
        "data.json",
    ]
    for name in candidates:
        candidate = vendor_dir / name
        if candidate.exists():
            return candidate
    json_files = [path for path in vendor_dir.glob("*.json") if path.is_file()]
    if json_files:
        return json_files[0]
    raise FileNotFoundError(f"No JSON dataset found in {vendor_dir}")


def _normalize_records(raw: Any) -> list[dict]:
    if isinstance(raw, dict):
        for key in ("verses", "data", "gita"):
            if key in raw:
                raw = raw[key]
                break
    if not isinstance(raw, list):
        raise ValueError("Vendor dataset must contain a list of verses.")
    return raw


def build_verses_json(vendor_dir: Path, output_path: Path) -> int:
    vendor_file = _find_vendor_json(vendor_dir)
    with vendor_file.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    records = _normalize_records(raw)
    output: list[dict] = []

    for index, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid verse record at index {index}.")
        chapter = _first_value(item, ("chapter", "chapter_number", "chapterNumber"))
        verse = _first_value(item, ("verse", "verse_number", "verseNumber"))
        sanskrit = _first_value(item, ("sanskrit", "slok", "shloka", "devanagari", "text"))
        translation = _first_value(item, ("translation_en", "translation", "english"))
        transliteration = _first_value(item, ("transliteration", "iast"))

        if chapter is None or verse is None:
            raise ValueError(f"Missing chapter/verse at index {index}.")
        chapter = int(chapter)
        verse = int(verse)
        sanskrit_text = str(sanskrit or "").strip()
        translation_text = str(translation or "").strip()
        if not sanskrit_text or not translation_text:
            raise ValueError(f"Missing text for {chapter}.{verse}.")

        record = {
            "chapter": chapter,
            "verse": verse,
            "sanskrit": sanskrit_text,
            "translation_en": translation_text,
        }
        transliteration_text = str(transliteration or "").strip()
        if transliteration_text:
            record["transliteration"] = transliteration_text

        output.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return len(output)
