#!/usr/bin/env python3
"""Build the light profile card from the dark card source."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"


REPLACEMENTS = {
    "#161b22": "#f6f8fa",
    "#0d1117": "#ffffff",
    "#30363d": "#d0d7de",
    "#e6edf3": "#24292f",
    "#768390": "#6e7781",
    "#ffa657": "#953800",
    "#a5d6ff": "#0550ae",
    "#7ee787": "#1a7f37",
    "#4f5863": "#8c959f",
    "#818b98": "#6e7781",
    "#b1bac4": "#57606a",
    "#f0f3f6": "#24292f",
}


def atomic_write(path: Path, content: str) -> None:
    """Write a complete file so an interrupted run cannot truncate the asset."""
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    source = (ASSETS / "mosaic-dark.svg").read_text(encoding="utf-8")
    light = source
    for dark, light_color in REPLACEMENTS.items():
        light = light.replace(dark, light_color)
    atomic_write(ASSETS / "mosaic-light.svg", light)


if __name__ == "__main__":
    main()
