from gita_autoposter.core.contracts import VersePayload, VerseRef


class VerseFetchAgent:
    def run(self, input: VerseRef, ctx) -> VersePayload:
        return VersePayload(
            verse_ref=input,
            sanskrit="dharma-kshetre kuru-kshetre samaveta yuyutsavah",
            translation="On the field of Dharma, on the field of Kurukshetra, gathered together, eager to fight.",
        )
