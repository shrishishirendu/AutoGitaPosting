from gita_autoposter.core.contracts import PostDraft, PostResult


class PosterAgent:
    def run(self, input: PostDraft, ctx) -> PostResult:
        if not ctx.config.dry_run:
            raise RuntimeError("Live posting not implemented in Milestone 1.")

        return PostResult(
            run_id=ctx.run_id,
            platform_ids={"instagram": "mock_ig_123", "facebook": "mock_fb_123"},
            status="success",
        )
