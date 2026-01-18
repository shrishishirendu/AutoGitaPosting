from gita_autoposter.core.contracts import PostDraft, PostPackageInput


class PostPackagerAgent:
    def run(self, input: PostPackageInput, ctx) -> PostDraft:
        return PostDraft(
            run_id=ctx.run_id,
            caption=input.commentary.caption,
            image_path=input.composed_image.path,
            status="draft",
        )
