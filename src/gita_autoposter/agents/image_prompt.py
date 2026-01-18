import hashlib

from gita_autoposter.core.contracts import Commentary, ImagePrompt


class ImagePromptAgent:
    def run(self, input: Commentary, ctx) -> ImagePrompt:
        prompt = (
            "A serene sunrise over a calm landscape, warm tones, minimalist style, "
            "evoking clarity and resolve."
        )
        signature = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return ImagePrompt(verse_ref=input.verse_ref, prompt=prompt, uniqueness_signature=signature)
