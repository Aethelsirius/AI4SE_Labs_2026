# Task 5 Report

## RAG coding agent

`run_rag_agent.py` reads the ten tasks in `missing_code.json` and processes them one at a time.
For each task it embeds the docstring and retrieves the five highest-scoring chunks from the Task 3 store.
The prompt contains the task description, the retrieved chunks with their paths and line ranges, and the full target file.
It asks for only the replacement method body, with no `def` line, imports, or explanation, so the response can be inserted without parsing Python.
The response is cleaned of Markdown fences or a repeated `def` line and indented to the body level.
It is then written over the `pass` statement in the requested class and method, leaving the rest of the file untouched.
Requests go to an OpenAI-compatible chat-completions endpoint.
The `--model` argument is restricted to the models allowed by the assignment, and this run used `gpt-4o-mini`.

The API key is read from `OPENAI_API_KEY`, which the script loads from `.env` if the variable is not already set.
All ten methods were filled in this way.

## Unit-test results

The suite uses the standard-library `unittest` runner:

```bash
cd Task_1/AI4SE_Playground/playground
python3 -m unittest discover -s tests -q
```

Result: `Ran 481 tests` with `OK`, so all 481 tests passed.
The generated sources were also checked with `python3 -m compileall`.
