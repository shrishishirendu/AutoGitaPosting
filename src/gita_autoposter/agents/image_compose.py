from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from gita_autoposter.core.contracts import ComposedImage, ImageComposeInput


class ImageComposeAgent:
    def run(self, input: ImageComposeInput, ctx) -> ComposedImage:
        output_dir = Path(ctx.artifact_dir) / "images" / "composed"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{ctx.run_id}_composed.png"

        image = Image.open(input.image.path_raw).convert("RGBA")
        draw = ImageDraw.Draw(image)

        text = input.verse_payload.sanskrit
        font_path = Path("fonts/NotoSansDevanagari-Regular.ttf")
        font_name = font_path.name if font_path.exists() else "default"
        font_size = max(28, image.width // 22)
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), size=font_size)
        else:
            font = ImageFont.load_default()

        margin = int(image.width * 0.08)
        max_width = image.width - (margin * 2)
        max_lines = 6
        lines = _wrap_text(text, draw, font, max_width)
        while len(lines) > max_lines and font_size > 20:
            font_size -= 2
            font = ImageFont.truetype(str(font_path), size=font_size) if font_path.exists() else ImageFont.load_default()
            lines = _wrap_text(text, draw, font, max_width)

        line_height = font.getbbox("Ag")[3] + 6
        text_height = line_height * len(lines)
        box_height = text_height + margin
        box_top = image.height - box_height - margin
        box_left = margin
        box_right = image.width - margin
        box_bottom = image.height - margin

        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            (box_left, box_top, box_right, box_bottom),
            fill=(0, 0, 0, 140),
        )
        image = Image.alpha_composite(image, overlay)
        draw = ImageDraw.Draw(image)

        y = box_top + (margin // 2)
        for line in lines:
            draw.text((box_left + margin // 2, y), line, fill=(255, 255, 255), font=font)
            y += line_height

        ref_text = f"Bhagavad Gita {input.verse_payload.verse_ref.chapter}.{input.verse_payload.verse_ref.verse}"
        ref_font_size = max(18, font_size - 10)
        ref_font = (
            ImageFont.truetype(str(font_path), size=ref_font_size)
            if font_path.exists()
            else ImageFont.load_default()
        )
        ref_width = _text_width(draw, ref_text, ref_font)
        draw.text(
            (image.width - margin - ref_width, image.height - margin - ref_font_size - 4),
            ref_text,
            fill=(255, 255, 255),
            font=ref_font,
        )

        image.convert("RGB").save(output_path)

        file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        return ComposedImage(
            run_id=ctx.run_id,
            path_composed=str(output_path),
            hash_composed=file_hash,
            overlay_text=text,
            font_name=font_name,
        )


def _wrap_text(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        current.append(word)
        test_line = " ".join(current)
        if _text_width(draw, test_line, font) > max_width and len(current) > 1:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> float:
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        return font.getbbox(text)[2]
