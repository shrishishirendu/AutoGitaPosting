from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from gita_autoposter.agents.image_compose import ImageComposeAgent
from gita_autoposter.agents.image_generate import ImageGenerateAgent
from gita_autoposter.agents.image_prompt import ImagePromptAgent
from gita_autoposter.core.config import Config
from gita_autoposter.core.contracts import (
    Commentary,
    ImageComposeInput,
    ImagePromptInput,
    ImagePrompt,
    VersePayload,
    VerseRef,
)
from gita_autoposter.core.visual_intent import resolve_visual_intent
from gita_autoposter.db import add_artifact, connect, init_db


def _make_commentary() -> Commentary:
    return Commentary(
        verse_ref=VerseRef(chapter=1, verse=1),
        social_en="Social insight.",
        professional_en="Professional insight.",
        practical_en="Practical insight. Action: do one thing.",
        caption_final_en="Stay clear and focused. Bhagavad Gita 1.1.",
        hashtags=["#gita", "#focus"],
        fingerprint="hash",
    )


def test_image_prompt_agent_generates_prompt(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type("Ctx", (), {"config": Config(), "db": conn, "run_id": "run-1"})
        payload = VersePayload(
            verse_ref=VerseRef(chapter=1, verse=1),
            ord_index=0,
            sanskrit="धृतराष्ट्र उवाच",
            translation="Dhritarashtra said",
        )
        commentary = _make_commentary()
        intent = resolve_visual_intent(payload, commentary)
        prompt_input = ImagePromptInput(
            verse_payload=payload,
            commentary=commentary,
            visual_intent=intent,
        )
        prompt = ImagePromptAgent().run(prompt_input, ctx)

    assert prompt.prompt_text
    assert prompt.fingerprint


def test_image_prompt_agent_retries_on_duplicate(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type("Ctx", (), {"config": Config(), "db": conn, "run_id": "run-1"})
        payload = VersePayload(
            verse_ref=VerseRef(chapter=1, verse=1),
            ord_index=0,
            sanskrit="धृतराष्ट्र उवाच",
            translation="Dhritarashtra said",
        )
        commentary = _make_commentary()
        intent = resolve_visual_intent(payload, commentary)
        prompt_input = ImagePromptInput(
            verse_payload=payload,
            commentary=commentary,
            visual_intent=intent,
        )
        first = ImagePromptAgent().run(prompt_input, ctx)
        add_artifact(
            conn,
            "run-old",
            "prompt",
            path="",
            hash_value="",
            created_at=datetime.utcnow(),
            prompt_text=first.prompt_text,
            prompt_fingerprint=first.fingerprint,
        )
        second = ImagePromptAgent().run(prompt_input, ctx)

    assert second.prompt_text != first.prompt_text


def test_image_generate_agent_creates_file(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type(
            "Ctx",
            (),
            {
                "config": Config(artifact_dir=str(tmp_path)),
                "db": conn,
                "run_id": "run-1",
                "artifact_dir": str(tmp_path),
            },
        )
        prompt = ImagePrompt(
            verse_ref=VerseRef(chapter=1, verse=1),
            prompt_text="Test prompt",
            style_profile="style",
            uniqueness_signature="sig",
            fingerprint=hashlib.sha256(b"Test prompt").hexdigest(),
        )
        artifact = ImageGenerateAgent().run(prompt, ctx)

    assert Path(artifact.path_raw).exists()
    assert len(artifact.hash_raw) == 64


def test_image_compose_agent_creates_composed(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type(
            "Ctx",
            (),
            {
                "config": Config(artifact_dir=str(tmp_path)),
                "db": conn,
                "run_id": "run-1",
                "artifact_dir": str(tmp_path),
            },
        )
        prompt = ImagePrompt(
            verse_ref=VerseRef(chapter=1, verse=1),
            prompt_text="Test prompt",
            style_profile="style",
            uniqueness_signature="sig",
            fingerprint=hashlib.sha256(b"Test prompt").hexdigest(),
        )
        raw = ImageGenerateAgent().run(prompt, ctx)
        payload = VersePayload(
            verse_ref=VerseRef(chapter=1, verse=1),
            ord_index=0,
            sanskrit="धृतराष्ट्र उवाच",
            translation="Dhritarashtra said",
        )
        composed = ImageComposeAgent().run(ImageComposeInput(verse_payload=payload, image=raw), ctx)

    assert Path(composed.path_composed).exists()
    assert composed.overlay_text == "धृतराष्ट्र उवाच"


def test_image_generate_uniqueness_retry(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with connect(str(db_path)) as conn:
        init_db(conn)
        ctx = type(
            "Ctx",
            (),
            {
                "config": Config(artifact_dir=str(tmp_path)),
                "db": conn,
                "run_id": "run-1",
                "artifact_dir": str(tmp_path),
            },
        )
        prompt = ImagePrompt(
            verse_ref=VerseRef(chapter=1, verse=1),
            prompt_text="Duplicate prompt",
            style_profile="style",
            uniqueness_signature="sig",
            fingerprint=hashlib.sha256(b"Duplicate prompt").hexdigest(),
        )
        first = ImageGenerateAgent().run(prompt, ctx)
        add_artifact(
            conn,
            "run-old",
            "generated",
            first.path_raw,
            first.hash_raw,
            first.created_at,
            path_raw=first.path_raw,
            hash_raw=first.hash_raw,
        )
        second = ImageGenerateAgent().run(prompt, ctx)
        assert second.hash_raw != first.hash_raw
