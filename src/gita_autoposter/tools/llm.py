from __future__ import annotations

import os
import re


class BaseLLM:
    def generate_text(self, prompt: str, temperature: float, max_tokens: int) -> str:
        raise NotImplementedError


class MockLLM(BaseLLM):
    def generate_text(self, prompt: str, temperature: float, max_tokens: int) -> str:
        match = re.search(r"Bhagavad Gita\s+(\d+)\.(\d+)", prompt)
        if match:
            chapter, verse = match.group(1), match.group(2)
        else:
            chapter, verse = "1", "1"
        verse_ref = f"Bhagavad Gita {chapter}.{verse}"

        social = (
            "Community grows when we honor shared purpose and avoid needless conflict. "
            "This verse reminds us to meet tension with clarity, not drama."
        )
        professional = (
            "In work, alignment matters more than noise. "
            "Choose goals that match your values and show up with steady focus."
        )
        practical = (
            "Create a short pause before you respond so you act with intention. "
            "Action: write down the single decision you will make today and the value it supports."
        )
        caption = (
            f"On difficult days, return to purpose and let it guide your next move. "
            f"Stay calm, act with clarity, and keep your integrity intact. {verse_ref}."
        )
        hashtags = "#bhagavadgita #mindfulness #clarity #purpose #leadership #focus #wisdom #dailypractice"

        return (
            "SOCIAL:\n"
            f"{social}\n"
            "PROFESSIONAL:\n"
            f"{professional}\n"
            "PRACTICAL:\n"
            f"{practical}\n"
            "CAPTION:\n"
            f"{caption}\n"
            "HASHTAGS:\n"
            f"{hashtags}\n"
        )


class PlaceholderOpenAIClient(BaseLLM):
    def generate_text(self, prompt: str, temperature: float, max_tokens: int) -> str:
        raise RuntimeError(
            "Real LLM calls are disabled. Set USE_REAL_LLM=true when implemented."
        )


def get_llm() -> BaseLLM:
    use_real = os.getenv("USE_REAL_LLM", "false").strip().lower() in {"1", "true", "yes"}
    if use_real:
        return PlaceholderOpenAIClient()
    return MockLLM()
