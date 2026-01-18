from gita_autoposter.core.contracts import PostDraft, PostPackageInput


class PostPackagerAgent:
    def run(self, input: PostPackageInput, ctx) -> PostDraft:
        hashtag_block = " ".join(input.commentary.hashtags)
        caption = input.commentary.caption_final_en
        if hashtag_block:
            caption = f"{caption}\n\n{hashtag_block}"
        return PostDraft(
            run_id=ctx.run_id,
            caption=caption,
            image_path=input.composed_image.path,
            status="draft",
            social_en=input.commentary.social_en,
            professional_en=input.commentary.professional_en,
            practical_en=input.commentary.practical_en,
            caption_final_en=input.commentary.caption_final_en,
            hashtags=input.commentary.hashtags,
            style_notes=input.commentary.style_notes,
            fingerprint=input.commentary.fingerprint,
        )
