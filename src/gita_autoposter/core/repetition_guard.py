from __future__ import annotations

import difflib
import re


def _normalize(text: str) -> str:
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return " ".join(tokens)


def similarity(a: str, b: str) -> float:
    normalized_a = _normalize(a)
    normalized_b = _normalize(b)
    if not normalized_a or not normalized_b:
        return 0.0
    return difflib.SequenceMatcher(None, normalized_a, normalized_b).ratio()


class RepetitionGuard:
    def __init__(self, threshold: float = 0.78, window: int = 20) -> None:
        self.threshold = threshold
        self.window = window

    def is_repetitive(self, caption: str, recent: list[str]) -> bool:
        for previous in recent[: self.window]:
            if similarity(caption, previous) >= self.threshold:
                return True
        return False
