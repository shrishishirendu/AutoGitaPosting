from gita_autoposter.core.contracts import SequenceSelection, VersePayload
from gita_autoposter.dataset import get_verse


class VerseFetchAgent:
    def run(self, input: SequenceSelection, ctx) -> VersePayload:
        record = get_verse(
            input.verse_ref.chapter,
            input.verse_ref.verse,
            ctx.config.gita_dataset_path,
        )
        return VersePayload(
            verse_ref=input.verse_ref,
            ord_index=input.ord_index,
            sanskrit=record["sanskrit"],
            translation=record["translation_en"],
        )
