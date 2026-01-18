from __future__ import annotations

import hashlib
from pathlib import Path

from gita_autoposter.core.contracts import ImageArtifact, ImagePrompt
from gita_autoposter.db import get_recent_image_hashes
from gita_autoposter.tools.image_provider import get_image_provider


class ImageGenerateAgent:
    def run(self, input: ImagePrompt, ctx) -> ImageArtifact:
        provider = get_image_provider()
        size = (ctx.config.image_size, ctx.config.image_size)
        output_dir = Path(ctx.artifact_dir) / "images" / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)

        image = provider.generate(input.prompt_text, size=size, seed=None)
        prompt_hash = hashlib.sha256(input.prompt_text.encode("utf-8")).hexdigest()
        output_path = output_dir / f"{ctx.run_id}_{prompt_hash[:10]}.png"
        image.save(output_path)

        file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        recent = set(get_recent_image_hashes(ctx.db, 30))
        if file_hash in recent:
            image = provider.generate(input.prompt_text, size=size, seed=1)
            output_path = output_dir / f"{ctx.run_id}_{prompt_hash[:10]}_retry.png"
            image.save(output_path)
            file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
            if file_hash in recent:
                print("Warning: duplicate image hash detected after retry.")

        return ImageArtifact(
            run_id=ctx.run_id,
            path_raw=str(output_path),
            hash_raw=file_hash,
            provider_name=provider.__class__.__name__,
        )
