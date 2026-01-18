from gita_autoposter.core.contracts import PostDraft, PostResult
from gita_autoposter.db import mark_verse_posted


class PosterAgent:
    def run(self, input: PostDraft, ctx) -> PostResult:
        if not ctx.config.dry_run:
            raise RuntimeError("Live posting not implemented in Milestone 1.")

        result = PostResult(
            run_id=ctx.run_id,
            platform_ids={"instagram": "mock_ig_123", "facebook": "mock_fb_123"},
            status="success",
        )
        mark_verse_posted(ctx.db, ctx.run_id)
        return result
