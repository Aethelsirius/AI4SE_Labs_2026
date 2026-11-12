#!/usr/bin/env python3
"""Create and query deterministic hashed-token embeddings for repository chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


EMBEDDING_DIMENSION = 256
TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+")


def embedding(text: str, dimensions: int = EMBEDDING_DIMENSION) -> list[float]:
    """Return a normalized hashed bag-of-tokens embedding."""
    vector = [0.0] * dimensions
    tokens = TOKEN_PATTERN.findall(text.lower())

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest, "big") % dimensions
        vector[bucket] += 1.0

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude:
        vector = [value / magnitude for value in vector]
    return vector


def create_store(chunks: list[dict]) -> list[dict]:
    """Attach an embedding to every chunk while retaining retrieval metadata."""
    return [
        {
            "id": chunk["id"],
            "path": chunk["path"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "content": chunk["content"],
            "embedding": embedding(chunk["content"]),
        }
        for chunk in chunks
    ]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Calculate cosine similarity for two vectors."""
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimension")
    return sum(a * b for a, b in zip(left, right))


def retrieve(store: list[dict], query: str, limit: int) -> list[dict]:
    """Return the most similar chunks for a natural-language query."""
    query_vector = embedding(query)
    ranked = sorted(
        (
            {
                **chunk,
                "similarity": cosine_similarity(query_vector, chunk["embedding"]),
            }
            for chunk in store
        ),
        key=lambda chunk: chunk["similarity"],
        reverse=True,
    )
    return ranked[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="create an embedding store")
    build.add_argument("chunks", type=Path, help="Task 2 chunks JSON file")
    build.add_argument("output", type=Path, help="embedding store JSON file")

    search = subparsers.add_parser("search", help="retrieve similar chunks")
    search.add_argument("store", type=Path, help="embedding store JSON file")
    search.add_argument("query", help="query text")
    search.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if args.command == "build":
        chunks = json.loads(args.chunks.read_text(encoding="utf-8"))
        store = create_store(chunks)
        args.output.write_text(
            json.dumps(store, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {len(store)} chunk embeddings to {args.output}")
    elif args.command == "search":
        if args.limit < 1:
            parser.error("--limit must be at least 1")
        store = json.loads(args.store.read_text(encoding="utf-8"))
        for chunk in retrieve(store, args.query, args.limit):
            print(
                f'{chunk["similarity"]:.4f} {chunk["path"]}:'
                f'{chunk["start_line"]}-{chunk["end_line"]}'
            )


if __name__ == "__main__":
    main()
