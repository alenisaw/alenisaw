# Setup

1. Create a public GitHub repository named exactly `alenisaw`.
2. Upload all files while preserving the folder structure.
3. Open **Actions** and run **Update profile card** once.
4. GitHub will display the repository `README.md` on your profile.

The portrait is generated entirely from ASCII characters. The SVG contains no
embedded raster image. Character density, edge direction, and per-character
color preserve the hood seams, shadowed face, white robe, and red collar.

The `<picture>` block switches between dark and light variants. GitHub Actions
refreshes repository, star, and follower counts once per day.

The dark SVG is the source card. Run `python build_profile.py` after changing
its layout to rebuild the light theme, then run `python update_stats.py` to
refresh the counters. The workflow performs both steps automatically.
