# Task 2 Report

## Chunking design

`chunk_repository.py` walks the repository recursively and sorts files by path before processing them, which keeps the output stable across runs.
It ignores anything under `.git` and rejects files containing a NUL byte as binary.
Files that fail UTF-8 decoding are dropped, because they cannot be read as source text.

Each remaining file is split into fixed windows of 80 lines, and the last window is shorter when the file does not divide evenly.
The windows do not overlap, so no code is stored or retrieved twice, though a construct is occasionally cut across two chunks.
Eighty lines keeps a class, a function, or a related group of tests together.
That size still avoids pulling most of a file into the prompt.
Line boundaries were preferred to character or syntax boundaries.
They are cheap to compute, and the recorded ranges can be quoted directly when inspecting a result.

## Chunk data structure

`chunks.json` is a flat JSON array with one object per chunk:

- `id`: relative path plus the line range, for example `playground/orders.py#lines-1-80`
- `path`: path relative to the repository root
- `start_line`, `end_line`: one-based inclusive line numbers
- `content`: the chunk text

The file was generated from the Task 1 clone with:

```bash
python3 chunk_repository.py ../Task_1/AI4SE_Playground chunks.json
```

The run produced 72 chunks across 27 files.
