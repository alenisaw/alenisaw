#!/usr/bin/env python3
"""Convert a reference image into a pixel mosaic for the profile card."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

# High-resolution square mosaic grid fitted to the left panel (584 x 645 px)
WIDTH, HEIGHT = 220, 243
PANEL_WIDTH, PANEL_HEIGHT = 584.0, 645.0
START_X, START_Y = 36.0, 35.5

# Theme palette hexes used by build_profile.py; avoid emitting exact matches inside avatar pixels.
THEME_COLORS = {
    (0x16, 0x1B, 0x22),
    (0x0D, 0x11, 0x17),
    (0x30, 0x36, 0x3D),
    (0xE6, 0xED, 0xF3),
    (0x76, 0x83, 0x90),
    (0xFF, 0xA6, 0x57),
    (0xA5, 0xD6, 0xFF),
    (0x7E, 0xE7, 0x87),
    (0x4F, 0x58, 0x63),
    (0x81, 0x8B, 0x98),
    (0xB1, 0xBA, 0xC4),
    (0xF0, 0xF3, 0xF6),
}


def _snap_channel(val: int, step: int = 4) -> int:
    snapped = (val + step // 2) // step * step
    return 255 if snapped > 255 else snapped


def _safe_color(r: int, g: int, b: int) -> str:
    r, g, b = _snap_channel(r), _snap_channel(g), _snap_channel(b)
    if (r, g, b) in THEME_COLORS:
        b = b + 1 if b < 255 else b - 1
    return f"#{r:02x}{g:02x}{b:02x}"


def render_avatar(source: Path) -> str:
    image = ImageOps.exif_transpose(Image.open(source).convert("RGB"))

    physical_aspect = PANEL_WIDTH / PANEL_HEIGHT
    preview_height = 1200
    preview_width = round(preview_height * physical_aspect)

    image = ImageOps.fit(
        image,
        (preview_width, preview_height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.48),
    )

    image = ImageEnhance.Color(image).enhance(1.10)
    # Subtle shadow lift preserves facial features under the hood without washing out blacks.
    shadow_lut = [min(255, int(((i / 255.0) ** 0.92) * 255)) for i in range(256)]
    image = image.point(shadow_lut * 3)
    image = image.filter(ImageFilter.UnsharpMask(radius=0.8, percent=35, threshold=4))
    image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    scale_x = PANEL_WIDTH / WIDTH
    scale_y = PANEL_HEIGHT / HEIGHT

    lines = [
        f'<g transform="translate({START_X},{START_Y}) scale({scale_x:.6f},{scale_y:.6f})" shape-rendering="crispEdges">'
    ]
    # Preserve full tonal precision on the face/hood region; merge near-identical runs elsewhere to keep SVG compact.
    face_x0, face_x1 = int(WIDTH * 0.30), int(WIDTH * 0.70)
    face_y0, face_y1 = int(HEIGHT * 0.06), int(HEIGHT * 0.42)

    for y in range(HEIGHT):
        x = 0
        while x < WIDTH:
            r0, g0, b0 = image.getpixel((x, y))
            in_face = face_x0 <= x <= face_x1 and face_y0 <= y <= face_y1
            tol = 1 if in_face else 4
            run = 1
            rs, gs, bs = r0, g0, b0
            while x + run < WIDTH:
                nx = x + run
                r1, g1, b1 = image.getpixel((nx, y))
                ntol = 1 if (face_x0 <= nx <= face_x1 and face_y0 <= y <= face_y1) else tol
                if max(abs(r1 - r0), abs(g1 - g0), abs(b1 - b0)) <= ntol:
                    rs += r1
                    gs += g1
                    bs += b1
                    run += 1
                else:
                    break
            color = _safe_color(rs // run, gs // run, bs // run)
            lines.append(f'<rect x="{x}" y="{y}" width="{run}" height="1.03" fill="{color}"/>')
            x += run
    lines.append("</g>")
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
