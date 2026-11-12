# Task 3 Report

## Embedding design

`embed_chunks.py` represents each chunk as a 256-dimensional hashed bag of tokens.
Text is lowercased and split into identifiers and numbers, and each token is then hashed with BLAKE2b.
The hash selects one of the 256 buckets, whose count is incremented.
The count vector is then L2-normalized so that cosine similarity reflects token distribution rather than chunk length.
This is a lexical representation: it captures shared names, keywords, and numbers, but not meaning.
A query phrased in different vocabulary than the code will therefore rank poorly.
The trade-off was deliberate, because a hashed representation needs no model download, external service, or training data and behaves identically on every machine.
BLAKE2b was chosen over Python's built-in `hash`, which is randomized per process and would make stored and query embeddings incompatible between runs.

## Storage and retrieval

`embeddings.json` stores one object per chunk, keeping the original `id`, `path`, `start_line`, `end_line`, and `content` alongside the 256 floats under `embedding`.
The `search` subcommand embeds a query and ranks every stored chunk by cosine similarity:

```bash
python3 embed_chunks.py search embeddings.json "order pricing" --limit 5
```

The scan is linear, which is adequate for the 72 chunks produced here and costs little more than reading the store.
A larger corpus would need a vector index, but that change can sit behind the same `retrieve` function without affecting the stored format.
The store was built with:

```bash
python3 embed_chunks.py build ../Task_2/chunks.json embeddings.json
```
