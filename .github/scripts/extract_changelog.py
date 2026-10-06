#!/usr/bin/env python3
"""CHANGELOG.md adott verziójának szakaszát kiírja GITHUB_OUTPUT formátumban (`notes`).
Használat: extract_changelog.py <tag>   (pl. v1.0.0)"""
import re
import sys
from pathlib import Path

version = (sys.argv[1] if len(sys.argv) > 1 else "").removeprefix("v")
lines = (Path(__file__).resolve().parents[2] / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()

body, capturing = [], False
for line in lines:
    m = re.match(r"^## \[(.+?)\]", line)
    if m:
        if capturing:
            break  # a következő verzió címe
        capturing = m.group(1) == version
        continue
    if capturing:
        body.append(line)

notes = "\n".join(body).strip() or "See the commit history for details."
print(f"notes<<CHANGELOG_EOF\n{notes}\nCHANGELOG_EOF")
