from __future__ import annotations

import hashlib
import os
import random
from typing import Tuple

from PIL import Image, ImageDraw, ImageFilter


class BaseImageProvider:
    def generate(self, prompt: str, size: Tuple[int, int], seed: int | None) -> Image.Image:
        raise NotImplementedError


class MockImageProvider(BaseImageProvider):
    def generate(self, prompt: str, size: Tuple[int, int], seed: int | None) -> Image.Image:
        base_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        base_seed = int(base_hash[:8], 16)
        if seed is not None:
            base_seed ^= seed
        rng = random.Random(base_seed)

        width, height = size
        image = Image.new("RGB", (width, height))
        pixels = image.load()

        start = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        end = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        for y in range(height):
            blend = y / max(height - 1, 1)
            color = (
                int(start[0] * (1 - blend) + end[0] * blend),
                int(start[1] * (1 - blend) + end[1] * blend),
                int(start[2] * (1 - blend) + end[2] * blend),
            )
            for x in range(width):
                pixels[x, y] = color

        draw = ImageDraw.Draw(image)
        horizon = int(height * 0.6)
        draw.rectangle((0, horizon, width, height), fill=(30, 30, 40))
        draw.ellipse(
            (
                width * 0.4,
                height * 0.25,
                width * 0.6,
                height * 0.45,
            ),
            fill=(230, 220, 200),
        )

        for _ in range(3):
            x = rng.randint(width // 6, width - width // 6)
            y = rng.randint(int(height * 0.55), int(height * 0.8))
            w = rng.randint(width // 12, width // 6)
            h = rng.randint(height // 8, height // 5)
            draw.rectangle((x - w, y - h, x + w, y + h), fill=(10, 10, 20))

        vignette = Image.new("L", (width, height), 0)
        vignette_draw = ImageDraw.Draw(vignette)
        vignette_draw.ellipse(
            (-width * 0.2, -height * 0.2, width * 1.2, height * 1.2),
            fill=220,
        )
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=width // 12))
        image = Image.composite(image, Image.new("RGB", (width, height), (0, 0, 0)), vignette)

        return image


class PlaceholderRealProvider(BaseImageProvider):
    def generate(self, prompt: str, size: Tuple[int, int], seed: int | None) -> Image.Image:
        raise NotImplementedError(
            "Real image provider is not implemented. Set USE_REAL_IMAGE_PROVIDER=false."
        )


def get_image_provider() -> BaseImageProvider:
    use_real = os.getenv("USE_REAL_IMAGE_PROVIDER", "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if use_real:
        return PlaceholderRealProvider()
    return MockImageProvider()
