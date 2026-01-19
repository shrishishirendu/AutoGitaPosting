from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    dry_run: bool = True
    db_path: str = "data/app.db"
    artifact_dir: str = "artifacts"
    sequence_xlsx_path: str = "data/sequence/verses.xlsx"
    gita_dataset_path: str = "data/gita/verses.json"
    use_real_image_provider: bool = False
    image_size: int = 1024
    timezone: str = "Australia/Sydney"
    post_time: str = "07:00"
    post_to_facebook: bool = True
    post_to_instagram: bool = True
    fb_page_id: str | None = None
    ig_user_id: str | None = None
    meta_access_token: str | None = None


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    load_dotenv()
    dry_run = _parse_bool(os.getenv("DRY_RUN"), True)
    db_path = os.getenv("DB_PATH", "data/app.db")
    artifact_dir = os.getenv("ARTIFACT_DIR", "artifacts")
    sequence_xlsx_path = os.getenv("SEQUENCE_XLSX_PATH", "data/sequence/verses.xlsx")
    gita_dataset_path = os.getenv("GITA_DATASET_PATH", "data/gita/verses.json")
    use_real_image_provider = _parse_bool(os.getenv("USE_REAL_IMAGE_PROVIDER"), False)
    image_size = int(os.getenv("IMAGE_SIZE", "1024"))
    timezone = os.getenv("TIMEZONE", "Australia/Sydney")
    post_time = os.getenv("POST_TIME", "07:00")
    post_to_facebook = _parse_bool(os.getenv("POST_TO_FACEBOOK"), True)
    post_to_instagram = _parse_bool(os.getenv("POST_TO_INSTAGRAM"), True)
    fb_page_id = os.getenv("FB_PAGE_ID")
    ig_user_id = os.getenv("IG_USER_ID")
    meta_access_token = os.getenv("META_ACCESS_TOKEN")
    return Config(
        dry_run=dry_run,
        db_path=db_path,
        artifact_dir=artifact_dir,
        sequence_xlsx_path=sequence_xlsx_path,
        gita_dataset_path=gita_dataset_path,
        use_real_image_provider=use_real_image_provider,
        image_size=image_size,
        timezone=timezone,
        post_time=post_time,
        post_to_facebook=post_to_facebook,
        post_to_instagram=post_to_instagram,
        fb_page_id=fb_page_id,
        ig_user_id=ig_user_id,
        meta_access_token=meta_access_token,
    )
