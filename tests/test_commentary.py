from __future__ import annotations

import re

from gita_autoposter.agents.commentary_agent import CommentaryAgent
from gita_autoposter.core.config import Config
from gita_autoposter.core.contracts import VersePayload, VerseRef
from gita_autoposter.core.repetition_guard import RepetitionGuard
from gita_autoposter.db import connect, init_db


def _sentence_count(text: str) -> int:
    parts = re.split(r"[.!?]+", text)
    return len([part for part in parts if part.strip()])


def test_commentary_agent_output(tmp_path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type("Ctx", (), {"config": Config(), "db": conn, "run_id": "run-1"})
        agent = CommentaryAgent()
        payload = VersePayload(
            verse_ref=VerseRef(chapter=1, verse=1),
            ord_index=0,
            sanskrit="धृतराष्ट्र उवाच",
            translation="Dhritarashtra said",
        )
        commentary = agent.run(payload, ctx)

    assert _sentence_count(commentary.social_en) >= 2
    assert _sentence_count(commentary.professional_en) >= 2
    assert _sentence_count(commentary.practical_en) >= 2
    assert "Action:" in commentary.practical_en
    assert "Bhagavad Gita 1.1" in commentary.caption_final_en
    assert 8 <= len(commentary.hashtags) <= 15


def test_repetition_guard_flags_similarity() -> None:
    guard = RepetitionGuard(threshold=0.7, window=5)
    base = "Return to purpose and let it guide your next move."
    near = "Return to purpose and let it guide your next move."
    different = "Change the structure and perspective entirely."

    assert guard.is_repetitive(near, [base])
    assert not guard.is_repetitive(different, [base])


def test_commentary_retry_sets_warning(tmp_path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type("Ctx", (), {"config": Config(), "db": conn, "run_id": "run-1"})
        agent = CommentaryAgent()
        payload = VersePayload(
            verse_ref=VerseRef(chapter=1, verse=1),
            ord_index=0,
            sanskrit="धृतराष्ट्र उवाच",
            translation="Dhritarashtra said",
        )
        first = agent.run(payload, ctx)
        conn.execute(
            "INSERT INTO drafts (run_id, caption, image_path, status, created_at, caption_final_en) "
            "VALUES (?, ?, ?, ?, datetime('now'), ?)",
            ("run-old", first.caption_final_en, "path.png", "success", first.caption_final_en),
        )
        conn.commit()

        second = agent.run(payload, ctx)

    assert second.style_notes is not None
