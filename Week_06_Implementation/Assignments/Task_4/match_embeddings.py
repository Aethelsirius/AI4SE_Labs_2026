#!/usr/bin/env python3
"""Retrieve the n most relevant chunks from a Task 3 embedding store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TASK_3_DIRECTORY = Path(__file__).parents[1] / "Task_3"
sys.path.insert(0, str(TASK_3_DIRECTORY))

from embed_chunks import cosine_similarity, embedding  # noqa: E402


def match_embedding(
    store: list[dict], input_embedding: list[float], count: int
) -> list[dict]:
    """Return up to count chunks ranked by cosine similarity."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if not store:
        return []

    dimension = len(input_embedding)
    if dimension == 0:
        raise ValueError("input embedding must not be empty")

    ranked = []
    for chunk in store:
        if len(chunk["embedding"]) != dimension:
            raise ValueError("input and stored embeddings must have the same dimension")
        ranked.append(
            {
                "id": chunk["id"],
                "path": chunk["path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "content": chunk["content"],
                "similarity": cosine_similarity(input_embedding, chunk["embedding"]),
            }
        )

    ranked.sort(key=lambda chunk: (-chunk["similarity"], chunk["id"]))
    return ranked[:count]


def match_query(store: list[dict], query: str, count: int) -> list[dict]:
    """Embed a text query and return its most relevant chunks."""
    return match_embedding(store, embedding(query), count)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", type=Path, help="Task 3 embedding store")
    parser.add_argument("query", help="natural-language task or search query")
    parser.add_argument("-n", "--count", type=int, default=5)
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    store = json.loads(args.store.read_text(encoding="utf-8"))
    for chunk in match_query(store, args.query, args.count):
        print(
            f'{chunk["similarity"]:.4f}\t{chunk["path"]}:'
            f'{chunk["start_line"]}-{chunk["end_line"]}\t{chunk["id"]}'
        )


if __name__ == "__main__":
    main()
