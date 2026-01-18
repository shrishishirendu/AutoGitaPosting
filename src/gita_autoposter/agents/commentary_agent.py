from __future__ import annotations

import hashlib

from gita_autoposter.content.commentary_prompt import build_prompt, parse_response
from gita_autoposter.core.contracts import Commentary, VersePayload
from gita_autoposter.core.repetition_guard import RepetitionGuard
from gita_autoposter.db import get_recent_captions
from gita_autoposter.tools.llm import get_llm


class CommentaryAgent:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.guard = RepetitionGuard()

    def run(self, input: VersePayload, ctx) -> Commentary:
        verse_ref = f"Bhagavad Gita {input.verse_ref.chapter}.{input.verse_ref.verse}"
        base_prompt = build_prompt(input.translation, verse_ref)
        parsed = self._generate_with_retry(base_prompt, ctx.db)
        caption = parsed["caption"]
        fingerprint = hashlib.sha256(caption.encode("utf-8")).hexdigest()

        return Commentary(
            verse_ref=input.verse_ref,
            social_en=parsed["social"],
            professional_en=parsed["professional"],
            practical_en=parsed["practical"],
            caption_final_en=caption,
            hashtags=parsed["hashtags"],
            style_notes=parsed.get("style_notes"),
            fingerprint=fingerprint,
        )

    def _generate_with_retry(self, prompt: str, conn) -> dict:
        parsed = self._generate(prompt)
        recent = get_recent_captions(conn, 20)
        if self.guard.is_repetitive(parsed["caption"], recent):
            retry_prompt = (
                f"{prompt}\n\nMake it feel distinctly different: vary the structure, "
                "avoid the same opener, and shift metaphors."
            )
            parsed_retry = self._generate(retry_prompt)
            if self.guard.is_repetitive(parsed_retry["caption"], recent):
                parsed_retry["style_notes"] = "Repetition warning: caption similar to recent."
            return parsed_retry
        return parsed

    def _generate(self, prompt: str) -> dict:
        raw = self.llm.generate_text(prompt, temperature=0.7, max_tokens=900)
        try:
            return parse_response(raw)
        except ValueError:
            return self._fallback(prompt)

    def _fallback(self, prompt: str) -> dict:
        verse_ref = "Bhagavad Gita 1.1"
        for line in prompt.splitlines():
            if line.startswith("Verse reference:"):
                verse_ref = line.split(":", 1)[1].strip()
                break
        social = "We thrive when our shared purpose is clear and our actions are measured."
        professional = "Clarity of intent keeps work honest and focused amid pressure."
        practical = (
            "Take a short pause before responding so your next step is intentional. "
            "Action: write down the one value your next decision should protect."
        )
        caption = (
            "Return to purpose and let it guide your next move. "
            f"Keep your response calm and your values intact. {verse_ref}."
        )
        return {
            "social": social,
            "professional": professional,
            "practical": practical,
            "caption": caption,
            "hashtags": [
                "#bhagavadgita",
                "#mindfulness",
                "#clarity",
                "#purpose",
                "#wisdom",
                "#dailypractice",
                "#focus",
                "#reflection",
            ],
        }
