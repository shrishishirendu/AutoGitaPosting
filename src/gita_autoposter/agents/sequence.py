from gita_autoposter.core.contracts import SequenceInput, SequenceSelection, VerseRef
from gita_autoposter.db import reserve_next_verse


class SequenceAgent:
    def run(self, input: SequenceInput, ctx) -> SequenceSelection:
        chapter, verse, ord_index = reserve_next_verse(ctx.db, input.run_id)
        return SequenceSelection(
            verse_ref=VerseRef(chapter=chapter, verse=verse),
            ord_index=ord_index,
        )
