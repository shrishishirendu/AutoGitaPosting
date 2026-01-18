from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from gita_autoposter.core.contracts import ComposedImage, ImageComposeInput


class ImageComposeAgent:
    def run(self, input: ImageComposeInput, ctx) -> ComposedImage:
        output_dir = Path(ctx.artifact_dir) / ctx.run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "composed.png"

        image = Image.open(input.image.path).convert("RGB")
        draw = ImageDraw.Draw(image)

        font_path = Path("assets/fonts/NotoSansDevanagari-Regular.ttf")
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), size=40)
            text = input.verse_payload.sanskrit
        else:
            font = ImageFont.load_default()
            text = "Verse overlay pending"

        draw.text((40, 900), text, fill=(10, 10, 10), font=font)
        image.save(output_path)

        file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        return ComposedImage(run_id=ctx.run_id, path=str(output_path), hash=file_hash)
