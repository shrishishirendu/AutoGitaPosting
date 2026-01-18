import hashlib
import difflib

from gita_autoposter.content.image_style import style_profile
from gita_autoposter.core.contracts import ImagePrompt, ImagePromptInput, IntentType
from gita_autoposter.db import get_recent_prompt_texts


class ImagePromptAgent:
    def run(self, input: ImagePromptInput, ctx) -> ImagePrompt:
        prompt_text = self._build_prompt(input)
        prompt_text, fingerprint, signature = self._ensure_novelty(prompt_text, ctx)
        return ImagePrompt(
            verse_ref=input.verse_payload.verse_ref,
            prompt_text=prompt_text,
            style_profile=style_profile,
            uniqueness_signature=signature,
            fingerprint=fingerprint,
        )

    def _ensure_novelty(self, prompt_text: str, ctx) -> tuple[str, str, str]:
        fingerprint = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        recent = get_recent_prompt_texts(ctx.db, 30)
        if self._is_similar(prompt_text, recent):
            retry_prompt = (
                f"{prompt_text} Change the setting, composition, metaphor, and palette."
            )
            fingerprint = hashlib.sha256(retry_prompt.encode("utf-8")).hexdigest()
            signature = hashlib.sha256(f"{retry_prompt}|signature".encode("utf-8")).hexdigest()
            return retry_prompt, fingerprint, signature
        signature = hashlib.sha256(f"{prompt_text}|signature".encode("utf-8")).hexdigest()
        return prompt_text, fingerprint, signature

    def _is_similar(self, prompt_text: str, recent: list[str]) -> bool:
        for prior in recent:
            if difflib.SequenceMatcher(None, prompt_text, prior).ratio() >= 0.78:
                return True
        return False

    def _build_prompt(self, input: ImagePromptInput) -> str:
        intent = input.visual_intent
        verse_ref = input.verse_payload.verse_ref
        ref_text = f"Bhagavad Gita {verse_ref.chapter}.{verse_ref.verse}"

        if intent.intent_type == IntentType.DIALOGUE:
            characters = ", ".join(intent.primary_characters) or "two characters"
            return (
                f"{style_profile} Depict a respectful dialogue between {characters}. "
                f"{intent.scene_description} Cinematic, spiritual atmosphere, no text."
            )
        if intent.intent_type == IntentType.CHAPTER_CONTEXT:
            return (
                f"{style_profile} Kurukshetra battlefield before war, dawn tension, "
                "chariots, flags, conches, subtle dust and light rays. No gore, no text."
            )
        if intent.intent_type == IntentType.SITUATIONAL:
            return (
                f"{style_profile} {intent.scene_description} Modern symbolic scene, "
                "soft light, contemplative mood, no text."
            )
        return (
            f"{style_profile} Divine Lord Krishna portrait, serene, radiant, timeless, "
            "respectful, high quality, not kitsch, no violence, no text. "
            f"Reference: {ref_text}."
        )
