#!/usr/bin/env python3
"""Resolve git conflict markers in text files.

Usage examples:
  python scripts/resolve_conflict_markers.py --strategy ours README.md app.py
  python scripts/resolve_conflict_markers.py --strategy theirs README.md
  python scripts/resolve_conflict_markers.py --strategy both README.md
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List


def resolve_text(text: str, strategy: str) -> str:
    lines = text.splitlines(keepends=True)
    out: List[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("<<<<<<< "):
            out.append(line)
            i += 1
            continue

        i += 1
        ours: List[str] = []
        while i < len(lines) and not lines[i].startswith("======="):
            ours.append(lines[i])
            i += 1
        if i >= len(lines):
            raise ValueError("Malformed conflict: missing =======")

        i += 1
        theirs: List[str] = []
        while i < len(lines) and not lines[i].startswith(">>>>>>>"):
            theirs.append(lines[i])
            i += 1
        if i >= len(lines):
            raise ValueError("Malformed conflict: missing >>>>>>>")

        i += 1

        if strategy == "ours":
            out.extend(ours)
        elif strategy == "theirs":
            out.extend(theirs)
        else:
            out.extend(ours)
            out.extend(theirs)

    return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve conflict markers in files.")
    parser.add_argument("--strategy", choices=["ours", "theirs", "both"], default="both")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    for file_name in args.files:
        path = Path(file_name)
        original = path.read_text(encoding="utf-8")
        resolved = resolve_text(original, args.strategy)
        path.write_text(resolved, encoding="utf-8")
        print(f"Resolved markers in {path} using strategy={args.strategy}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
