from gita_autoposter.core.contracts import SequenceSelection, VersePayload


class VerseFetchAgent:
    def run(self, input: SequenceSelection, ctx) -> VersePayload:
        return VersePayload(
            verse_ref=input.verse_ref,
            sanskrit="dharma-kshetre kuru-kshetre samaveta yuyutsavah",
            translation="On the field of Dharma, on the field of Kurukshetra, gathered together, eager to fight.",
        )
