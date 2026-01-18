from __future__ import annotations

import re

from gita_autoposter.core.contracts import IntentType, VisualIntent, VersePayload, Commentary


def resolve_visual_intent(verse_payload: VersePayload, commentary: Commentary) -> VisualIntent:
    translation = verse_payload.translation.lower()
    sanskrit = verse_payload.sanskrit
    chapter = verse_payload.verse_ref.chapter
    verse = verse_payload.verse_ref.verse

    if _is_dialogue(translation, sanskrit):
        characters = _resolve_characters(chapter, verse, translation, commentary)
        scene = _dialogue_scene_description(characters)
        return VisualIntent(
            intent_type=IntentType.DIALOGUE,
            primary_characters=characters,
            scene_description=scene,
            confidence=0.9,
            rationale="Dialogue detected via verse keywords.",
        )

    if chapter == 1:
        intent = VisualIntent(
            intent_type=IntentType.CHAPTER_CONTEXT,
            primary_characters=[],
            scene_description="Kurukshetra battlefield before war, tense dawn atmosphere.",
            confidence=0.7,
            rationale="Chapter 1 context bias applied.",
        )
        return _apply_confidence_floor(intent)

    situational = _situational_scene_from_commentary(commentary)
    base_intent = VisualIntent(
        intent_type=IntentType.SITUATIONAL,
        primary_characters=[],
        scene_description=situational,
        confidence=0.6,
        rationale="Situational scene inferred from commentary.",
    )
    if "uncertain" in situational.lower():
        base_intent.confidence = 0.4
    return _apply_confidence_floor(base_intent)


def _apply_confidence_floor(intent: VisualIntent) -> VisualIntent:
    if intent.confidence < 0.55:
        return VisualIntent(
            intent_type=IntentType.DIVINE_FALLBACK,
            primary_characters=["Krishna"],
            scene_description="Serene, radiant, timeless image of Lord Krishna.",
            confidence=0.4,
            rationale="Low confidence; divine fallback applied.",
        )
    return intent


def _is_dialogue(translation: str, sanskrit: str) -> bool:
    if "उवाच" in sanskrit:
        return True
    keywords = ("said", "asked", "spoke", "replied")
    return any(word in translation for word in keywords)


def _resolve_characters(chapter: int, verse: int, translation: str, commentary: Commentary) -> list[str]:
    if chapter == 1 and verse == 1:
        return ["Dhritarashtra", "Sanjaya"]

    characters = []
    if re.search(r"\bkrishna\b", translation) or "Krishna" in commentary.caption_final_en:
        characters.append("Krishna")
    if re.search(r"\barjuna\b", translation) or "Arjuna" in commentary.caption_final_en:
        characters.append("Arjuna")

    if characters:
        return characters[:2]
    return ["Two characters"]


def _dialogue_scene_description(characters: list[str]) -> str:
    if "Dhritarashtra" in characters and "Sanjaya" in characters:
        return "Royal palace chamber, Dhritarashtra speaking with Sanjaya."
    if "Krishna" in characters and "Arjuna" in characters:
        return "Chariot at the battlefield, Krishna advising Arjuna."
    return "Two figures in respectful conversation, spiritual atmosphere."


def _situational_scene_from_commentary(commentary: Commentary) -> str:
    text = " ".join(
        [
            commentary.social_en,
            commentary.professional_en,
            commentary.practical_en,
            commentary.caption_final_en,
        ]
    ).lower()
    keywords = _extract_keywords(text)
    if "integrity" in keywords or "duty" in keywords:
        return "Modern workplace decision moment, calm and reflective tone."
    if "fear" in keywords or "hesitation" in keywords:
        return "Solitary figure at a crossroads, soft dawn light."
    if "clarity" in keywords or "focus" in keywords:
        return "Quiet room with a journal and warm light, centered composition."
    return "Uncertain abstract scenario; suggest calm, symbolic spiritual setting."


def _extract_keywords(text: str) -> set[str]:
    candidates = {"hesitation", "duty", "fear", "integrity", "clarity", "focus", "purpose"}
    words = set(re.findall(r"[a-z]+", text))
    return candidates.intersection(words)
