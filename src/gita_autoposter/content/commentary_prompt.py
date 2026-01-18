from __future__ import annotations

import re

from gita_autoposter.content.style_guide import banned_openers, caption_length_max, caption_length_min, tone_rules


def build_prompt(translation: str, verse_ref: str) -> str:
    banned_text = ", ".join(banned_openers)
    tone_text = "\n".join(f"- {rule}" for rule in tone_rules)
    return (
        "You are writing a short, modern commentary for a Bhagavad Gita verse.\n"
        f"Verse reference: {verse_ref}\n"
        f"Verse translation: {translation}\n\n"
        "Write three short sections:\n"
        "- SOCIAL: 2-4 sentences\n"
        "- PROFESSIONAL: 2-4 sentences\n"
        "- PRACTICAL: 2-4 sentences plus one concrete action step.\n\n"
        "Then write CAPTION: a flowing IG/FB caption that combines the three ideas without labels.\n"
        f"Caption length target: {caption_length_min}-{caption_length_max} characters.\n"
        "Mention the verse reference exactly once in the caption.\n\n"
        "Tone rules:\n"
        f"{tone_text}\n"
        f"Avoid these openers: {banned_text}\n\n"
        "Output exactly in this format:\n"
        "SOCIAL:\n"
        "<text>\n"
        "PROFESSIONAL:\n"
        "<text>\n"
        "PRACTICAL:\n"
        "<text>\n"
        "CAPTION:\n"
        "<text>\n"
        "HASHTAGS:\n"
        "<space-separated hashtags>\n"
    )


def parse_response(text: str) -> dict:
    sections = {}
    current = None
    for line in text.splitlines():
        label = line.strip().rstrip(":").upper()
        if label in {"SOCIAL", "PROFESSIONAL", "PRACTICAL", "CAPTION", "HASHTAGS"}:
            current = label
            sections[current] = []
            continue
        if current:
            sections[current].append(line.strip())

    if not sections:
        raise ValueError("LLM response did not contain expected sections.")

    def _join(key: str) -> str:
        return " ".join(part for part in sections.get(key, []) if part).strip()

    parsed = {
        "social": _join("SOCIAL"),
        "professional": _join("PROFESSIONAL"),
        "practical": _join("PRACTICAL"),
        "caption": _join("CAPTION"),
        "hashtags": _join("HASHTAGS"),
    }

    if not parsed["social"] or not parsed["professional"] or not parsed["practical"]:
        raise ValueError("Missing commentary sections in LLM response.")
    if not parsed["caption"]:
        raise ValueError("Missing caption in LLM response.")

    hashtags = re.findall(r"#\w+", parsed["hashtags"])
    parsed["hashtags"] = hashtags
    return parsed
