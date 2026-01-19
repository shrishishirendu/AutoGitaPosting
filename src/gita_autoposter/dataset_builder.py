from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_verses_json(csv_path: Path, output_path: Path) -> int:
    frame = pd.read_csv(csv_path, encoding="utf-8")
    normalized = {
        " ".join(str(col).strip().lower().split()): col for col in frame.columns
    }

    def _pick_column(candidates: list[str]) -> str | None:
        for candidate in candidates:
            key = " ".join(candidate.strip().lower().split())
            if key in normalized:
                return normalized[key]
        return None

    column_map = {
        "chapter_number": _pick_column(["Chapter"]),
        "verse_number": _pick_column(["Verse"]),
        "sanskrit": _pick_column(["Sanskrit Anuvad"]),
        "english_translation": _pick_column(
            ["English Translation", "Enlgish Translation"]
        ),
    }
    missing = [key for key, value in column_map.items() if value is None]
    if missing:
        raise ValueError(
            "CSV is missing required columns: " + ", ".join(missing)
        )

    frame = frame.rename(columns={value: key for key, value in column_map.items()})
    frame = frame[list(column_map.keys())]

    def _extract_last_number(series: pd.Series) -> pd.Series:
        return (
            series.astype(str)
            .str.findall(r"\d+")
            .str[-1]
        )

    frame["chapter_number"] = pd.to_numeric(
        _extract_last_number(frame["chapter_number"]), errors="coerce"
    )
    frame["verse_number"] = pd.to_numeric(
        _extract_last_number(frame["verse_number"]), errors="coerce"
    )
    frame["sanskrit"] = frame["sanskrit"].fillna("").astype(str).str.strip()
    frame["english_translation"] = (
        frame["english_translation"].fillna("").astype(str).str.strip()
    )
    frame = frame.dropna(subset=["chapter_number", "verse_number"])
    frame["chapter_number"] = frame["chapter_number"].astype(int)
    frame["verse_number"] = frame["verse_number"].astype(int)

    frame = frame.sort_values(["chapter_number", "verse_number"], kind="mergesort")
    frame = frame.drop_duplicates(
        subset=["chapter_number", "verse_number"], keep="first"
    )

    output = [
        {
            "chapter_number": int(row.chapter_number),
            "verse_number": int(row.verse_number),
            "sanskrit": str(row.sanskrit),
            "english_translation": str(row.english_translation),
        }
        for row in frame.itertuples(index=False)
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return len(output)
