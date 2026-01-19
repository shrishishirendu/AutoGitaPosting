from __future__ import annotations

from datetime import datetime

from gita_autoposter.agents.poster import PosterAgent
from gita_autoposter.core.config import Config
from gita_autoposter.core.contracts import PostDraft
from gita_autoposter.db import connect, init_db


def _insert_reserved(conn, run_id: str) -> None:
    conn.execute(
        "INSERT INTO verse_history (chapter_number, verse_number, ord_index, run_id, status, reserved_at) "
        "VALUES (?, ?, ?, ?, 'RESERVED', ?)",
        (1, 1, 0, run_id, datetime.utcnow().isoformat()),
    )
    conn.commit()


def test_poster_dry_run_updates_db(tmp_path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        run_id = "run-1"
        conn.execute(
            "INSERT INTO drafts (run_id, caption, image_path, status, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, "caption", "image.png", "draft", datetime.utcnow().isoformat()),
        )
        _insert_reserved(conn, run_id)
        ctx = type("Ctx", (), {"config": Config(), "db": conn, "run_id": run_id})

        result = PosterAgent().run(
            PostDraft(run_id=run_id, caption="caption", image_path="image.png", status="draft"),
            ctx,
        )

        row = conn.execute(
            "SELECT status, facebook_post_id, instagram_post_id, error_message FROM drafts WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        history = conn.execute(
            "SELECT status FROM verse_history WHERE run_id = ?",
            (run_id,),
        ).fetchone()

    assert result.status == "posted"
    assert row["status"] == "posted"
    assert row["facebook_post_id"] == f"mock_fb_{run_id}"
    assert row["instagram_post_id"] == f"mock_ig_{run_id}"
    assert row["error_message"] is None
    assert history["status"] == "POSTED"


def test_poster_failure_preserves_reservation(tmp_path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        run_id = "run-2"
        conn.execute(
            "INSERT INTO drafts (run_id, caption, image_path, status, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, "caption", "image.png", "draft", datetime.utcnow().isoformat()),
        )
        _insert_reserved(conn, run_id)
        config = Config(dry_run=False, post_to_facebook=True, post_to_instagram=False)
        ctx = type("Ctx", (), {"config": config, "db": conn, "run_id": run_id})

        try:
            PosterAgent().run(
                PostDraft(run_id=run_id, caption="caption", image_path="image.png", status="draft"),
                ctx,
            )
        except ValueError:
            pass

        row = conn.execute(
            "SELECT status, error_message FROM drafts WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        history = conn.execute(
            "SELECT status FROM verse_history WHERE run_id = ?",
            (run_id,),
        ).fetchone()

    assert row["status"] == "failed"
    assert row["error_message"]
    assert history["status"] == "RESERVED"
