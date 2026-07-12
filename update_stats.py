#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path

USERNAME = "alenisaw"
ASSETS = Path(__file__).resolve().parent / "assets"


def github_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "alenisaw-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def fetch_stats() -> dict[str, int]:
    profile = github_json(f"https://api.github.com/users/{USERNAME}")
    repos = int(profile.get("public_repos", 0))
    followers = int(profile.get("followers", 0))

    stars = 0
    page = 1
    while True:
        repositories = github_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?type=owner&per_page=100&page={page}"
        )
        if not repositories:
            break

        stars += sum(
            int(repository.get("stargazers_count", 0))
            for repository in repositories
        )

        if len(repositories) < 100:
            break
        page += 1

    return {
        "repo_data": repos,
        "star_data": stars,
        "follower_data": followers,
        "following_data": int(profile.get("following", 0)),
        "gist_data": int(profile.get("public_gists", 0)),
    }


def patch_svg(path: Path, stats: dict[str, int]) -> None:
    content = path.read_text(encoding="utf-8")

    for element_id, value in stats.items():
        pattern = rf'(<tspan id="{element_id}">)[^<]*(</tspan>)'
        content, replacements = re.subn(
            pattern,
            rf'\g<1>{value}\g<2>',
            content,
        )
        if replacements != 1:
            raise RuntimeError(
                f"Expected exactly one {element_id} in {path}, "
                f"found {replacements}."
            )

    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    stats = fetch_stats()
    for filename in ("mosaic-dark.svg", "mosaic-light.svg"):
        patch_svg(ASSETS / filename, stats)
        updated = (ASSETS / filename).read_text(encoding="utf-8")
        for element_id, value in stats.items():
            if updated.count(f'id="{element_id}">{value}</tspan>') != 1:
                raise RuntimeError(f"Could not verify {element_id} in {filename}.")
    print(json.dumps(stats, sort_keys=True))


if __name__ == "__main__":
    main()
