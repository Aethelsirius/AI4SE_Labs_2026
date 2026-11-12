# Task 4 Report

## Matching design

`match_embeddings.py` ranks the Task 3 store against an input embedding with cosine similarity.
The stored vectors are already normalized, so the cosine is just the dot product.
Matching therefore needs one multiply-and-add per dimension and no extra normalization step.
Results are sorted by descending similarity, and ties are broken by chunk `id` so the output order is reproducible.
`match_embedding` takes a precomputed vector and checks its dimension against each stored vector.
`match_query` is a thin wrapper that embeds a text query with the same function used in Task 3.
The CLI exposes the query path and prints similarity, path, line range, and id for the top `n` results.

Example:

```bash
python3 match_embeddings.py ../Task_3/embeddings.json "fix order pricing" --count 5
```

The matcher scans the full store, which is exact and has no index to build or maintain.
For 72 chunks the cost is negligible, and an approximate index would only pay off at a much larger corpus size.
