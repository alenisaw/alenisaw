#!/usr/bin/env python3
"""Convert a reference image into a full-color symbol mosaic for the profile card."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

# High-resolution spatial sampling grid constants (176 x 100 = 17,600 cells)
WIDTH, HEIGHT = 176, 100
FONT_SIZE, LINE_HEIGHT, TEXT_LENGTH = 8.0, 6.45, 584.0
START_X, START_Y = 36.0, 34.0


def render_avatar(source: Path) -> str:
    image = ImageOps.exif_transpose(Image.open(source).convert("RGB"))

    # Stage 1: Fit source image strictly to the PHYSICAL visual SVG aspect ratio (584 / (100 * 6.45))
    physical_aspect = TEXT_LENGTH / (HEIGHT * LINE_HEIGHT)
    preview_height = 1000
    preview_width = round(preview_height * physical_aspect)

    image = ImageEnhance.Color(image).enhance(1.15)
    image = ImageEnhance.Contrast(image).enhance(1.06)

    # Crop to physical portrait ratio preserving exact current framing and zoom
    image = ImageOps.fit(
        image,
        (preview_width, preview_height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.48),
    )

    # Stage 2: Sharpening pre-filter to retain hood/clothing/facial detail
    image = image.filter(
        ImageFilter.UnsharpMask(
            radius=1.0,
            percent=110,
            threshold=2,
        )
    )

    # Stage 3: Resample aspect-correct image into high-density grid (176 x 100)
    image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # Stage 4: High color resolution quantization (128 colors)
    image = image.quantize(colors=128, method=Image.Quantize.MEDIANCUT).convert("RGB")

    lines: list[str] = []
    for row in range(HEIGHT):
        parts = [
            f'<text x="{START_X}" y="{START_Y + row * LINE_HEIGHT:.2f}" '
            f'class="ascii" style="font-size:{FONT_SIZE}px" '
            f'textLength="{TEXT_LENGTH}" lengthAdjust="spacingAndGlyphs" '
            'xml:space="preserve">'
        ]
        for column in range(WIDTH):
            red, green, blue = image.getpixel((column, row))
            parts.append(f'<tspan fill="#{red:02x}{green:02x}{blue:02x}">█</tspan>')
        parts.append("</text>")
        lines.append("".join(parts))
    return "\n".join(lines)


def replace_avatar(svg: Path, avatar: str) -> None:
    content = svg.read_text(encoding="utf-8")
    pattern = r"<!-- AVATAR_START -->.*?<!-- AVATAR_END -->"
    replacement = f"<!-- AVATAR_START -->\n{avatar}\n<!-- AVATAR_END -->"
    updated, replacements = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
    if replacements != 1:
        raise RuntimeError(
            f"Could not find <!-- AVATAR_START --> ... <!-- AVATAR_END --> markers in {svg}."
        )
    svg.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to the reference image")
    args = parser.parse_args()
    replace_avatar(ASSETS / "mosaic-dark.svg", render_avatar(args.source))


if __name__ == "__main__":
    main()
