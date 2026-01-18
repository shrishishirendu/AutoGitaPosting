from gita_autoposter.core.contracts import Commentary, VersePayload


class CommentaryAgent:
    def run(self, input: VersePayload, ctx) -> Commentary:
        social = "Choose your battles with integrity and clarity."
        professional = "Align your work with your values before taking action."
        practical = "Pause, gather your focus, then move with purpose."
        caption = (
            f"{input.translation}\n\n"
            f"Social: {social}\n"
            f"Professional: {professional}\n"
            f"Practical: {practical}"
        )
        return Commentary(
            verse_ref=input.verse_ref,
            social=social,
            professional=professional,
            practical=practical,
            caption=caption,
        )
