from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class MetaApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class MetaApiClient:
    dry_run: bool

    def post_facebook_page_photo(
        self, page_id: str, access_token: str, image_path: str, caption: str
    ) -> dict[str, Any]:
        if self.dry_run:
            return {"post_id": "mock_fb_post_123"}

        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        with open(image_path, "rb") as handle:
            files = {"source": handle}
            data = {"access_token": access_token, "caption": caption}
            response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code >= 400:
            raise MetaApiError(response.text, response.status_code)
        return response.json()

    def post_instagram_photo(
        self, ig_user_id: str, access_token: str, image_path: str, caption: str
    ) -> dict[str, Any]:
        if self.dry_run:
            return {"ig_media_id": "mock_ig_media_123", "ig_post_id": "mock_ig_post_123"}

        if not image_path.startswith("http"):
            raise MetaApiError(
                "Instagram Graph API requires a public image URL. Provide a hosted URL.",
                None,
            )

        container_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
        container_data = {
            "image_url": image_path,
            "caption": caption,
            "access_token": access_token,
        }
        container_response = requests.post(container_url, data=container_data, timeout=30)
        if container_response.status_code >= 400:
            raise MetaApiError(container_response.text, container_response.status_code)
        container_id = container_response.json().get("id")

        publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
        publish_data = {"creation_id": container_id, "access_token": access_token}
        publish_response = requests.post(publish_url, data=publish_data, timeout=30)
        if publish_response.status_code >= 400:
            raise MetaApiError(publish_response.text, publish_response.status_code)
        return {
            "ig_media_id": container_id,
            "ig_post_id": publish_response.json().get("id"),
        }
