#!/usr/bin/env python3
"""Split a repository's text files into line-oriented JSON chunks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CHUNK_LINES = 80


def is_text_file(path: Path) -> bool:
    """Return whether path can be safely read as UTF-8 text."""
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return b"\x00" not in data


def chunk_file(path: Path, repository_root: Path, chunk_lines: int) -> list[dict]:
    """Create line-based chunks for one text file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    relative_path = path.relative_to(repository_root).as_posix()
    chunks = []

    for start in range(0, len(lines), chunk_lines):
        end = min(start + chunk_lines, len(lines))
        chunks.append(
            {
                "id": f"{relative_path}#lines-{start + 1}-{end}",
                "path": relative_path,
                "start_line": start + 1,
                "end_line": end,
                "content": "\n".join(lines[start:end]),
            }
        )

    return chunks


def build_chunks(repository_root: Path, chunk_lines: int) -> list[dict]:
    """Walk a repository deterministically and return all text-file chunks."""
    chunks = []
    files = sorted(
        path
        for path in repository_root.rglob("*")
        if path.is_file()
        and ".git" not in path.relative_to(repository_root).parts
        and is_text_file(path)
    )

    for path in files:
        try:
            chunks.extend(chunk_file(path, repository_root, chunk_lines))
        except UnicodeDecodeError:
            continue

    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chunk a repository's UTF-8 text files into JSON."
    )
    parser.add_argument("repository", type=Path, help="repository directory to read")
    parser.add_argument("output", type=Path, help="JSON file to write")
    parser.add_argument(
        "--chunk-lines",
        type=int,
        default=DEFAULT_CHUNK_LINES,
        help=f"maximum lines per chunk (default: {DEFAULT_CHUNK_LINES})",
    )
    args = parser.parse_args()

    if args.chunk_lines < 1:
        parser.error("--chunk-lines must be at least 1")
    if not args.repository.is_dir():
        parser.error(f"repository is not a directory: {args.repository}")

    chunks = build_chunks(args.repository, args.chunk_lines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(chunks)} chunks to {args.output}")


if __name__ == "__main__":
    main()
