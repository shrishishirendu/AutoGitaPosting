from __future__ import annotations

from gita_autoposter.core.contracts import Commentary, IntentType, VersePayload, VerseRef
from gita_autoposter.core.visual_intent import resolve_visual_intent


def _commentary() -> Commentary:
    return Commentary(
        verse_ref=VerseRef(chapter=1, verse=1),
        social_en="Social reflection.",
        professional_en="Professional reflection.",
        practical_en="Practical reflection. Action: do one thing.",
        caption_final_en="Stay focused. Bhagavad Gita 1.1.",
        hashtags=["#gita"],
        fingerprint="hash",
    )


def test_visual_intent_dialogue() -> None:
    payload = VersePayload(
        verse_ref=VerseRef(chapter=1, verse=1),
        ord_index=0,
        sanskrit="धृतराष्ट्र उवाच",
        translation="Dhritarashtra said",
    )
    intent = resolve_visual_intent(payload, _commentary())
    assert intent.intent_type == IntentType.DIALOGUE
    assert intent.confidence == 0.9


def test_visual_intent_fallback_low_confidence() -> None:
    payload = VersePayload(
        verse_ref=VerseRef(chapter=2, verse=1),
        ord_index=0,
        sanskrit="अज्ञात",
        translation="Unknown",
    )
    commentary = _commentary()
    commentary.caption_final_en = "Abstract insight."
    intent = resolve_visual_intent(payload, commentary)
    assert intent.intent_type == IntentType.DIVINE_FALLBACK
    assert intent.confidence == 0.4
