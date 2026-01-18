from gita_autoposter.core.contracts import SequenceInput, VerseRef


class SequenceAgent:
    def run(self, input: SequenceInput, ctx) -> VerseRef:
        return VerseRef(chapter=1, verse=1)
