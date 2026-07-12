#!/usr/bin/env python3
"""Convert a reference image into a full-color symbol mosaic for the profile card."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
WIDTH, HEIGHT = 108, 67
FONT_SIZE, LINE_HEIGHT, TEXT_LENGTH = 11.0, 8.25, 440.0


def render_avatar(source: Path) -> str:
    image = ImageOps.exif_transpose(Image.open(source).convert("RGB"))
    image = ImageEnhance.Color(image).enhance(1.18)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    image = image.quantize(colors=64, method=Image.Quantize.MEDIANCUT).convert("RGB")

    lines: list[str] = []
    start_x, start_y = 38.0, 90.0
    for row in range(HEIGHT):
        parts = [
            f'<text x="{start_x}" y="{start_y + row * LINE_HEIGHT:.2f}" '
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
    pattern = r'<text x="[^"]+" y="[^"]+" class="ascii".*?</text>\s*(?=<text x="548" y="50")'
    updated, replacements = re.subn(pattern, avatar + "\n", content, count=1, flags=re.DOTALL)
    if replacements != 1:
        raise RuntimeError(f"Could not find the avatar block in {svg}.")
    svg.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to the reference image")
    args = parser.parse_args()
    replace_avatar(ASSETS / "mosaic-dark.svg", render_avatar(args.source))


if __name__ == "__main__":
    main()
