from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw

from gita_autoposter.core.contracts import ImageArtifact, ImagePrompt


class ImageGenerateAgent:
    def run(self, input: ImagePrompt, ctx) -> ImageArtifact:
        output_dir = Path(ctx.artifact_dir) / ctx.run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        base_hash = hashlib.sha256(input.prompt.encode("utf-8")).hexdigest()
        output_path = output_dir / f"generated_{base_hash[:8]}.png"

        image = Image.new("RGB", (1080, 1080), color=(245, 240, 230))
        draw = ImageDraw.Draw(image)
        draw.text((40, 40), "Generated placeholder", fill=(20, 20, 20))
        image.save(output_path)

        file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        return ImageArtifact(run_id=ctx.run_id, path=str(output_path), hash=file_hash)
