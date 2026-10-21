from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".txt", ".eml", ".md"}
CHUNK_TARGET_CHARS = 12000
DECORATION_RE = re.compile(r"^[=\-*\s]+$")
HEADER_KEYS = ("From", "To", "Subject", "Date")


@dataclass(frozen=True)
class WorkItem:
    doc_id: str
    chunk_id: str
    path: str
    title: str
    kind: str
    text: str


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not DECORATION_RE.match(stripped):
            return stripped[:120]
    return ""


def _parse_eml(text: str) -> tuple[str, str]:
    messages: list[str] = []
    subjects: list[str] = []
    for raw in re.split(r"(?m)^===\s*$", text):
        block = raw.strip()
        if not block:
            continue
        headers: dict[str, str] = {}
        body_lines: list[str] = []
        in_headers = True
        for line in block.splitlines():
            if in_headers and line.strip() == "":
                in_headers = False
                continue
            if in_headers:
                for key in HEADER_KEYS:
                    if line.lower().startswith(key.lower() + ":"):
                        headers[key] = line.split(":", 1)[1].strip()
                        break
                else:
                    if body_lines or not messages:
                        in_headers = False
                        body_lines.append(line)
            else:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        meta = ", ".join(f"{k}: {headers[k]}" for k in HEADER_KEYS if k in headers)
        messages.append(f"[{meta}]\n{body}".strip())
        if "Subject" in headers and not subjects:
            subjects.append(headers["Subject"])
    title = subjects[0] if subjects else ""
    return title, "\n\n---\n\n".join(messages)


def _parse_txt(text: str) -> tuple[str, str]:
    return _first_meaningful_line(text), text.strip()


def _chunk(text: str, target: int = CHUNK_TARGET_CHARS) -> list[str]:
    if len(text) <= target:
        return [text]
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for para in paragraphs:
        if current and size + len(para) > target:
            chunks.append("\n\n".join(current))
            current, size = [], 0
        current.append(para)
        size += len(para) + 2
    if current:
        chunks.append("\n\n".join(current))
    return [c for c in chunks if c.strip()]


def load_corpus(input_dir: Path) -> tuple[list[dict], list[WorkItem]]:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"input directory not found: {input_dir}")
    paths = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not paths:
        raise FileNotFoundError(f"no supported documents in {input_dir}")

    docs: list[dict] = []
    items: list[WorkItem] = []
    for index, path in enumerate(paths, start=1):
        doc_id = f"D{index:02d}"
        rel = path.relative_to(input_dir).as_posix()
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".eml":
            kind = "email"
            title, body = _parse_eml(raw)
        else:
            kind = "text"
            title, body = _parse_txt(raw)
        title = title or path.stem
        chunks = _chunk(body)
        docs.append({
            "id": doc_id,
            "path": rel,
            "title": title,
            "kind": kind,
            "chars": len(body),
            "chunks": len(chunks),
            "preview": body[:200].replace("\n", " "),
        })
        for idx, chunk in enumerate(chunks, start=1):
            suffix = f".c{idx}" if len(chunks) > 1 else ""
            items.append(WorkItem(
                doc_id=doc_id,
                chunk_id=f"{doc_id}{suffix}",
                path=rel,
                title=title,
                kind=kind,
                text=chunk,
            ))
    return docs, items
