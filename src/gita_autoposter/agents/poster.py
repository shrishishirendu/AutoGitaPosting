import time
from datetime import datetime
from zoneinfo import ZoneInfo

from gita_autoposter.core.contracts import PostDraft, PostResult
from gita_autoposter.db import mark_verse_posted, set_post_results
from gita_autoposter.tools.meta_api import MetaApiClient, MetaApiError


class PosterAgent:
    def run(self, input: PostDraft, ctx) -> PostResult:
        client = MetaApiClient(dry_run=ctx.config.dry_run)
        timezone = ZoneInfo(ctx.config.timezone)
        posted_time = datetime.now(timezone).isoformat()
        facebook_post_id = None
        instagram_post_id = None

        try:
            if not ctx.config.dry_run:
                if ctx.config.post_to_facebook and not ctx.config.fb_page_id:
                    raise ValueError("FB_PAGE_ID is required for live posting.")
                if ctx.config.post_to_instagram and not ctx.config.ig_user_id:
                    raise ValueError("IG_USER_ID is required for live posting.")
                if (ctx.config.post_to_facebook or ctx.config.post_to_instagram) and not ctx.config.meta_access_token:
                    raise ValueError("META_ACCESS_TOKEN is required for live posting.")

            if ctx.config.post_to_facebook:
                if ctx.config.dry_run:
                    facebook_post_id = f"mock_fb_{ctx.run_id}"
                else:
                    facebook_post_id = _with_retries(
                        lambda: client.post_facebook_page_photo(
                            ctx.config.fb_page_id or "",
                            ctx.config.meta_access_token or "",
                            input.image_path,
                            input.caption,
                        )
                    ).get("post_id")

            if ctx.config.post_to_instagram:
                if ctx.config.dry_run:
                    instagram_post_id = f"mock_ig_{ctx.run_id}"
                else:
                    ig_result = _with_retries(
                        lambda: client.post_instagram_photo(
                            ctx.config.ig_user_id or "",
                            ctx.config.meta_access_token or "",
                            input.image_path,
                            input.caption,
                        )
                    )
                    instagram_post_id = ig_result.get("ig_post_id") or ig_result.get("ig_media_id")

            status = "posted"
            set_post_results(
                ctx.db,
                ctx.run_id,
                status,
                posted_time,
                facebook_post_id,
                instagram_post_id,
                None,
            )
            mark_verse_posted(ctx.db, ctx.run_id)
            return PostResult(
                run_id=ctx.run_id,
                platform_ids={
                    "facebook": facebook_post_id or "",
                    "instagram": instagram_post_id or "",
                },
                status=status,
            )
        except Exception as exc:  # noqa: BLE001
            set_post_results(
                ctx.db,
                ctx.run_id,
                "failed",
                None,
                facebook_post_id,
                instagram_post_id,
                str(exc),
            )
            raise


def _with_retries(func):
    delays = [1, 3, 9]
    last_exc: Exception | None = None
    for attempt, delay in enumerate(delays, start=1):
        try:
            return func()
        except MetaApiError as exc:
            if exc.status_code in {401, 403}:
                raise
            last_exc = exc
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        print(f"Attempt {attempt} failed, retrying in {delay}s")
        time.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("Unknown posting error.")
