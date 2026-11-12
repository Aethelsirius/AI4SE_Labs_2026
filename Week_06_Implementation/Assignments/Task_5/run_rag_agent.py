#!/usr/bin/env python3
"""Use the local RAG store and an OpenAI-compatible chat API to fill methods."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

ASSIGNMENTS_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = ASSIGNMENTS_ROOT / "Task_1" / "AI4SE_Playground"
SOURCE_ROOT = PROJECT_ROOT
MISSING_CODE = ASSIGNMENTS_ROOT / "missing_code.json"
EMBEDDING_STORE = ASSIGNMENTS_ROOT / "Task_3" / "embeddings.json"
MATCHER_ROOT = ASSIGNMENTS_ROOT / "Task_4"
sys.path.insert(0, str(MATCHER_ROOT))

from match_embeddings import match_query  # noqa: E402

ALLOWED_MODELS = {
    "gpt-6-luna",
    "gpt-5.6-luna",
    "gpt-5.4-nano",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4.1-nano",
    "gpt-4o-mini",
}
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without printing their values."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def call_llm(endpoint: str, api_key: str, model: str, prompt: str) -> str:
    """Request a method body from the configured chat-completions endpoint."""
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You implement exactly one missing Python method. Return only "
                    "the method body, without markdown fences, the def line, or "
                    "explanation. The body must be valid Python and use the existing "
                    "types, helpers, and exception conventions."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM request failed with HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"LLM request failed: {error.reason}") from error

    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("LLM response did not contain message content") from error


def clean_body(response: str) -> list[str]:
    """Extract code lines from a model response and remove common formatting."""
    response = response.strip()
    fenced = re.fullmatch(r"```(?:python)?\s*(.*?)```", response, re.DOTALL)
    if fenced:
        response = fenced.group(1).strip()
    if response.startswith("def ") or response.startswith("async def "):
        response = response[response.index("\n") + 1 :]
    lines = textwrap.dedent(response).splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or all(not line.strip() for line in lines):
        raise ValueError("LLM returned an empty method body")
    return lines


def build_prompt(task: dict, source: str, chunks: list[dict]) -> str:
    """Construct a grounded implementation prompt."""
    context = "\n\n".join(
        f"CHUNK {chunk['path']}:{chunk['start_line']}-{chunk['end_line']}\n"
        f"{chunk['content']}"
        for chunk in chunks
    )
    return (
        f"Implement `{task['class']}.{task['method']}` in `{task['file']}`.\n"
        f"Required behavior/documentation:\n{task['docstring']}\n\n"
        f"Relevant repository chunks:\n{context}\n\n"
        f"Full target file:\n{source}\n\n"
        "Return only the replacement body for the method. Do not modify any "
        "other method or add imports."
    )


def replace_pass_body(path: Path, class_name: str, method_name: str, body: list[str]) -> None:
    """Replace the pass-only body of the requested method."""
    lines = path.read_text(encoding="utf-8").splitlines()
    class_seen = False
    method_seen = False
    method_indent = 0
    pass_index = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped.startswith(f"class {class_name}(") or stripped == f"class {class_name}:":
            class_seen = True
        elif class_seen and stripped.startswith(f"def {method_name}("):
            method_seen = True
            method_indent = indent
        elif method_seen and stripped == "pass":
            pass_index = index
            break
        elif method_seen and stripped and indent <= method_indent:
            break

    if pass_index is None:
        raise ValueError(f"could not find pass-only body for {class_name}.{method_name}")

    body_indent = " " * (method_indent + 4)
    lines[pass_index : pass_index + 1] = [
        body_indent + line if line else "" for line in body
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(model: str, endpoint: str) -> None:
    """Process every entry in missing_code.json."""
    if model not in ALLOWED_MODELS:
        raise ValueError(f"model must be one of: {', '.join(sorted(ALLOWED_MODELS))}")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    store = json.loads(EMBEDDING_STORE.read_text(encoding="utf-8"))
    tasks = json.loads(MISSING_CODE.read_text(encoding="utf-8"))
    for task in tasks:
        target = SOURCE_ROOT / task["file"]
        source = target.read_text(encoding="utf-8")
        chunks = match_query(store, task["docstring"], 5)
        prompt = build_prompt(task, source, chunks)
        body = clean_body(call_llm(endpoint, api_key, model, prompt))
        replace_pass_body(target, task["class"], task["method"], body)
        print(f"Implemented {task['class']}.{task['method']} in {task['file']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--endpoint", default=os.environ.get("OPENAI_BASE_URL", DEFAULT_ENDPOINT))
    args = parser.parse_args()
    load_dotenv(ASSIGNMENTS_ROOT / ".env")
    run(args.model, args.endpoint)


if __name__ == "__main__":
    main()
