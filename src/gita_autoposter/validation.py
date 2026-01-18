from __future__ import annotations

from gita_autoposter.dataset import load_dataset
from gita_autoposter.db import get_queue_pairs


def find_missing_verses(conn, dataset_path: str) -> list[tuple[int, int]]:
    dataset = load_dataset(dataset_path)
    missing: list[tuple[int, int]] = []
    for chapter, verse, _ord_index in get_queue_pairs(conn):
        if (chapter, verse) not in dataset:
            missing.append((chapter, verse))
    return missing
