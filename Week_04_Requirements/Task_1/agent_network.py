from __future__ import annotations

import argparse
import json
import operator
import os
import re
import sys
import time
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path
from typing import Any, Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

try:
    from langgraph.types import Send
except ImportError:
    from langgraph.graph import Send

from ingest import load_corpus

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_MODELS = {
    "extract": "gpt-5.6-luna",
    "consolidate": "gpt-5.6-luna",
    "adjudicate": "gpt-5-mini",
    "review": "gpt-6-luna",
}

PRIORITY_SCALE = {
    "P1": "Must have - critical for core operation, legal/audit compliance, or data "
          "integrity; blocking for the first release.",
    "P2": "Should have - important for the daily workflows of key stakeholders; "
          "implement in the first release if feasible.",
    "P3": "Could have - valuable enhancement; schedule when capacity allows.",
    "P4": "Later - nice-to-have or speculative; keep in the backlog.",
}

BLACKLIST_CATEGORIES = ("conflicting", "nonsensical", "irrelevant", "superseded", "other")

BATCH_SIZE = 55
MAX_REFS_PER_REQ = 12

PRIORITY_ALIASES = {
    "p1": "P1", "1": "P1", "must": "P1", "critical": "P1", "must have": "P1",
    "p2": "P2", "2": "P2", "high": "P2", "should": "P2", "should have": "P2",
    "p3": "P3", "3": "P3", "medium": "P3", "could": "P3", "could have": "P3",
    "p4": "P4", "4": "P4", "low": "P4", "later": "P4", "nice to have": "P4",
}


class State(TypedDict, total=False):
    input_dir: str
    max_iterations: int
    models: dict
    docs: list
    work_items: list
    raw_candidates: Annotated[list, operator.add]
    extract_notes: Annotated[list, operator.add]
    candidates: list
    batches: list
    batch_drafts_raw: Annotated[list, operator.add]
    batch_drafts: list
    system_summary: str
    glossary: list
    requirements: list
    blacklist: list
    validate_issues: list
    adjudicate_issues: list
    audit_issues: list
    review_issues: list
    review_pass: bool
    review_log: list
    iteration: int
    untraced_docs: list
    uncovered_refs: list
    rendered_md: str


def log(msg: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {msg}", flush=True)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def make_chat(model: str, temperature: bool = True) -> ChatOpenAI:
    kwargs: dict[str, Any] = {"model": model, "timeout": 600}
    if temperature and not model.startswith("gpt-6"):
        kwargs["temperature"] = 0
    if os.environ.get("OPENAI_BASE_URL"):
        kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
    return ChatOpenAI(**kwargs)


def _message_text(resp: Any) -> str:
    content = getattr(resp, "content", resp)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()
    start = min((i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1), default=-1)
    if start == -1:
        raise ValueError("no JSON object/array found")
    opener = cleaned[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_str = False
    escape = False
    for pos in range(start, len(cleaned)):
        ch = cleaned[pos]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start:pos + 1])
    raise ValueError("unbalanced JSON")


def chat_json(node: str, system: str, user: str, model: str,
              default: Any, attempts: int = 3) -> Any:
    chat = make_chat(model)
    messages = [("system", system), ("human", user)]
    last_error: Exception | None = None
    last_text = ""
    for attempt in range(attempts):
        try:
            last_text = _message_text(chat.invoke(messages))
            return extract_json(last_text)
        except Exception as exc:
            last_error = exc
            log(f"  {node}: attempt {attempt + 1} failed: {type(exc).__name__}: {exc}")
            if "temperature" in str(exc).lower():
                chat = make_chat(model, temperature=False)
                continue
            if attempt == 0:
                messages = [
                    ("system", system),
                    ("human", user),
                    ("ai", last_text[:4000]),
                    ("human", f"Your reply could not be parsed as JSON ({exc}). "
                              "Reply again with ONLY valid JSON, no prose, no code fences."),
                ]
            time.sleep(2 ** attempt)
    log(f"  {node}: giving up, using fallback ({last_error})")
    return default


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _clean_str(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "shall",
    "must", "should", "will", "can", "may", "system", "support", "supporting",
    "allow", "enable", "provide", "user", "users", "using", "use", "used",
    "also", "such", "their", "they", "them", "when", "where", "which", "have",
    "has", "are", "was", "were", "all", "any", "each", "other", "more",
    "than", "not", "but", "its", "our", "your", "per", "via", "within",
}


def _terms(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", str(text or "").lower()):
        if len(token) < 3 or token in _STOPWORDS:
            continue
        if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
            token = token[:-1]
        tokens.add(token)
    return tokens


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _quote_in_text(quote: str, doc_text: str) -> bool:
    if not quote or not doc_text:
        return False
    return _normalize_text(quote) in _normalize_text(doc_text)


def _candidate_index(state: State) -> dict[str, dict]:
    return {c["ref"]: c for c in state.get("candidates", []) if c.get("ref")}


def _doc_texts(state: State) -> dict[str, str]:
    parts: dict[str, list[str]] = {}
    for item in state.get("work_items", []):
        if isinstance(item, dict) and item.get("doc_id") and item.get("text"):
            parts.setdefault(item["doc_id"], []).append(item["text"])
    return {doc_id: "\n".join(chunks) for doc_id, chunks in parts.items()}


def _ground_source_quote(source: dict, req: dict, ref_index: dict[str, dict],
                         doc_texts: dict[str, str]) -> str:
    doc_id = source["doc_id"]
    doc_text = doc_texts.get(doc_id, "")
    req_terms = _terms(
        f"{req.get('name', '')} {' '.join(req.get('keywords') or [])} "
        f"{req.get('explanation', '')}"
    )
    best: tuple[tuple[int, int], str] | None = None
    for ref in source.get("cands") or []:
        cand = ref_index.get(ref)
        if not cand or cand.get("doc_id") != doc_id:
            continue
        quote = _clean_str(cand.get("quote"), 300)
        if not quote or not _quote_in_text(quote, doc_text):
            continue
        overlap = len(req_terms & _terms(f"{cand.get('text', '')} {quote}"))
        score = (overlap, len(quote))
        if best is None or score > best[0]:
            best = (score, quote)
    if best:
        return best[1]
    quote = _clean_str(source.get("quote"), 300)
    if quote and _quote_in_text(quote, doc_text):
        return quote
    return ""


def _ground_sources(reqs: list, ref_index: dict[str, dict],
                    doc_texts: dict[str, str]) -> None:
    for req in reqs:
        for source in req.get("sources", []):
            if isinstance(source, dict):
                source["quote"] = _ground_source_quote(source, req, ref_index, doc_texts)


def _refs_in_requirements(reqs: list) -> set[str]:
    return {
        _clean_str(ref)
        for req in reqs
        for source in _as_list(req.get("sources"))
        if isinstance(source, dict)
        for ref in _as_list(source.get("cands"))
        if _clean_str(ref)
    }


def _refs_in_blacklist(blacklist: list) -> set[str]:
    return {
        _clean_str(ref)
        for item in blacklist
        for ref in _as_list(item.get("cands"))
        if _clean_str(ref)
    }


def _batch_ref_info(state: State) -> dict[str, dict]:
    info: dict[str, dict] = {}
    for draft in state.get("batch_drafts", []):
        for dr in _as_list(draft.get("requirements")):
            if not isinstance(dr, dict):
                continue
            area = _clean_str(dr.get("area"), 60).lower()
            for source in _as_list(dr.get("sources")):
                if not isinstance(source, dict):
                    continue
                doc_id = _clean_str(source.get("doc_id"))
                for ref in _as_list(source.get("cands")):
                    ref = _clean_str(ref)
                    if ref:
                        info[ref] = {"doc_id": doc_id, "area": area}
    return info


def _reattach_uncovered(state: State, reqs: list, blacklist: list,
                        ref_index: dict[str, dict],
                        doc_texts: dict[str, str]) -> tuple[int, list[str]]:
    covered_req = _refs_in_requirements(reqs)
    covered_bl = _refs_in_blacklist(blacklist)
    all_refs = {c["ref"] for c in state.get("candidates", []) if c.get("ref")}
    uncovered = sorted(all_refs - covered_req - covered_bl)
    ref_info = _batch_ref_info(state)
    reattached = 0

    for ref in list(uncovered):
        cand = ref_index.get(ref)
        if not cand:
            continue
        info = ref_info.get(ref, {})
        doc_id = cand.get("doc_id", "")
        quote = _clean_str(cand.get("quote"), 300)
        if quote and not _quote_in_text(quote, doc_texts.get(doc_id, "")):
            quote = ""
        cand_terms = _terms(f"{cand.get('text', '')} {cand.get('quote', '')}")
        best: tuple[int, int, dict] | None = None
        for req in reqs:
            req_terms = _terms(
                f"{req.get('name', '')} {' '.join(req.get('keywords') or [])} "
                f"{req.get('explanation', '')}"
            )
            overlap = len(cand_terms & req_terms)
            doc_match = any(
                isinstance(source, dict) and source.get("doc_id") == doc_id
                for source in _as_list(req.get("sources"))
            )
            area_match = bool(info.get("area")) and (
                _clean_str(req.get("area")).lower() == info["area"]
            )
            score = overlap * 3 + (2 if area_match else 0) + (1 if doc_match else 0)
            if best is None or score > best[0]:
                best = (score, overlap, req)
        if best is None or best[0] < 6 or best[1] < 2:
            continue
        req = best[2]
        sources = req.setdefault("sources", [])
        target = next(
            (s for s in sources if isinstance(s, dict) and s.get("doc_id") == doc_id),
            None,
        )
        if target is None:
            target = {"doc_id": doc_id, "quote": quote, "cands": []}
            sources.append(target)
        cands = target.setdefault("cands", [])
        if ref not in cands:
            cands.append(ref)
        uncovered.remove(ref)
        reattached += 1

    return reattached, uncovered


def _renumber(reqs: list) -> None:
    for idx, req in enumerate(reqs, start=1):
        req["id"] = f"REQ-{idx:03d}"


def _candidate_name(text: str) -> str:
    name = _clean_str(text, 160)
    name = re.sub(
        r"^(?:the\s+)?(?:system|application|software)\s+(?:shall|must|should|will)\s+",
        "", name, flags=re.I,
    )
    name = re.sub(r"^be able to\s+", "", name, flags=re.I)
    name = " ".join(name.split()[:10]).rstrip(".")
    return _clean_str(name[:1].upper() + name[1:], 80) or "Additional corpus requirement"


def _materialize_uncovered(state: State, reqs: list, ref_index: dict[str, dict],
                           doc_texts: dict[str, str],
                           uncovered: list[str]) -> list[dict]:
    if not uncovered:
        return reqs
    clusters: list[dict] = []
    for ref in uncovered:
        cand = ref_index.get(ref)
        if not cand:
            continue
        terms = _terms(f"{cand.get('text', '')} {cand.get('quote', '')}")
        cluster = next(
            (
                c for c in clusters
                if c["terms"] and terms
                and len(c["terms"] & terms) / len(c["terms"] | terms) >= 0.5
            ),
            None,
        )
        if cluster is None:
            clusters.append({"terms": terms, "refs": [ref]})
        else:
            cluster["refs"].append(ref)

    for cluster in clusters:
        texts: list[str] = []
        by_doc: dict[str, dict] = {}
        for ref in cluster["refs"]:
            cand = ref_index[ref]
            doc_id = _clean_str(cand.get("doc_id"))
            if doc_id not in by_doc:
                by_doc[doc_id] = {"doc_id": doc_id, "quote": "", "cands": []}
            by_doc[doc_id]["cands"].append(ref)
            text = _clean_str(cand.get("text"), 300)
            if text and text not in texts:
                texts.append(text)
        if not by_doc or not texts:
            continue
        explanation = " ".join(texts[:3])
        if explanation.count(".") < 2:
            explanation = explanation.rstrip(".") + ". This capability is required by the source corpus."
        first = ref_index[cluster["refs"][0]]
        keywords = sorted(_terms(texts[0]))[:5]
        entry = {
            "id": "",
            "name": _candidate_name(first.get("text", "")),
            "area": "general",
            "explanation": explanation,
            "priority": "P3",
            "keywords": keywords,
            "sources": list(by_doc.values()),
        }
        _ground_sources([entry], ref_index, doc_texts)
        reqs.append(entry)
    return reqs


def _scrub_refs(text: str, valid_req_ids: set[str], valid_refs: set[str]) -> str:
    text = re.sub(
        r"REQ-\d{3}",
        lambda m: m.group(0) if m.group(0) in valid_req_ids
        else "the discarded draft requirement",
        text,
    )
    return re.sub(
        r"C\d{4}",
        lambda m: m.group(0) if m.group(0) in valid_refs else "the discarded candidate",
        text,
    )


_ABSENCE_CLAIM_RE = re.compile(
    r"(does not appear|not (?:appear|present|found)\b|not in the (?:supplied )?corpus|"
    r"no supporting source|no traceable source|without any traceable source|"
    r"unsupported|invented requirement|unmapped candidate)",
    re.I,
)


def _sanitize_blacklist(items: list, known_docs: set[str],
                        ref_index: dict[str, dict], doc_texts: dict[str, str],
                        valid_req_ids: set[str],
                        covered_req: set[str]) -> list[dict]:
    valid_refs = set(ref_index)
    sanitized: list[dict] = []
    seen: set[tuple] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        origin = _clean_str(item.get("origin"))
        name = _clean_str(item.get("name"), 160)
        reason = _clean_str(item.get("reason"), 500)
        if not origin and reason.startswith("Discarded by deterministic validation:"):
            origin = "validation"
        category = _clean_str(item.get("category")).lower()
        if category not in BLACKLIST_CATEGORIES:
            category = "other"
        false_absence = (
            origin != "validation"
            and category in {"nonsensical", "other"}
            and bool(_ABSENCE_CLAIM_RE.search(f"{name} {reason}"))
        )

        cands: list[str] = []
        for raw_ref in _as_list(item.get("cands")):
            ref = _clean_str(raw_ref)
            if ref not in ref_index or ref in covered_req or ref in cands:
                continue
            if false_absence:
                cand = ref_index[ref]
                cand_doc = _clean_str(cand.get("doc_id"))
                cand_quote = _clean_str(cand.get("quote"), 300)
                if cand_doc in known_docs and _quote_in_text(
                    cand_quote, doc_texts.get(cand_doc, "")
                ):
                    continue
            cands.append(ref)

        doc_id = _clean_str(item.get("doc_id"))
        if doc_id not in known_docs:
            doc_id = ""
        if cands:
            doc_id = doc_id or _clean_str(ref_index[cands[0]].get("doc_id"))

        quote = _clean_str(item.get("quote"), 300)
        if cands:
            quote = next(
                (_clean_str(ref_index[ref].get("quote"), 300) for ref in cands
                 if _quote_in_text(_clean_str(ref_index[ref].get("quote"), 300),
                                   doc_texts.get(doc_id, ""))),
                "",
            )
        elif not (doc_id and quote and _quote_in_text(quote, doc_texts.get(doc_id, ""))):
            quote = ""

        if not cands and origin != "validation" and not (doc_id and quote):
            continue

        if not name and cands:
            name = _clean_str(ref_index[cands[0]].get("text"), 160)
        if not name:
            continue
        if not reason:
            reason = "Discarded without a stated reason."

        name = _scrub_refs(name, valid_req_ids, valid_refs)
        reason = _scrub_refs(reason, valid_req_ids, valid_refs)
        key = tuple(sorted(cands)) if cands else (
            "no-cands",
            _normalize_text(name),
            _normalize_text(reason),
        )
        if key in seen:
            continue
        seen.add(key)
        entry = {
            "name": name,
            "category": category,
            "reason": reason,
            "doc_id": doc_id,
            "quote": quote,
            "cands": cands,
        }
        if origin:
            entry["origin"] = origin
        sanitized.append(entry)

    return [
        {"id": f"BL-{idx:03d}", **entry}
        for idx, entry in enumerate(sanitized, start=1)
    ]


def _coverage_issues(uncovered: list[str], untraced: list[str]) -> list[dict]:
    issues: list[dict] = []
    if uncovered:
        preview = ", ".join(uncovered[:15]) + ("…" if len(uncovered) > 15 else "")
        issues.append({
            "kind": "coverage",
            "detail": f"{len(uncovered)} candidate refs not covered by any requirement "
                      f"or blacklist entry: {preview}",
        })
    if untraced:
        issues.append({
            "kind": "trace",
            "detail": "Documents with candidates that are cited by neither requirements "
                      f"nor blacklist: {', '.join(untraced)}",
        })
    return issues


def _merge_issues(*groups: list) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for issue in _as_list(group):
            if not isinstance(issue, dict):
                continue
            key = (_clean_str(issue.get("kind")), _clean_str(issue.get("detail")))
            if key in seen:
                continue
            seen.add(key)
            merged.append(issue)
    return merged


def ingest_node(state: State) -> dict:
    docs, items = load_corpus(Path(state["input_dir"]))
    log(f"ingest: {len(docs)} documents, {len(items)} work items")
    return {
        "docs": docs,
        "work_items": [vars(item) for item in items],
        "iteration": 0,
        "review_log": [],
        "review_pass": False,
    }


def fan_out(state: State):
    model = state.get("models", DEFAULT_MODELS)["extract"]
    return [Send("extract", {**item, "model": model}) for item in state["work_items"]]


def extract_node(item: dict) -> dict:
    system = (
        "You are a meticulous software requirements analyst. You receive ONE document "
        "(or one chunk of a larger document) from a corpus about a library management "
        "system (ILS) and its reporting/management tools. Extract every CANDIDATE "
        "REQUIREMENT it contains.\n"
        "Rules:\n"
        "- Include every statement expressing a need or desire for the future software: "
        "features, reports, data needs, constraints, quality attributes, and policies "
        "the system must enforce (including 'the system shall/must/should' statements).\n"
        "- One atomic requirement per item (split sentences joined by 'and/or' when they "
        "ask for distinct capabilities).\n"
        "- 'text': your paraphrase as ONE requirement sentence, preferably starting with "
        "'The system ...'.\n"
        "- 'quote': a SHORT verbatim snippet (max 30 words) from the document that "
        "evidences the requirement. It must appear character-for-character in the text.\n"
        "- 'note': one sentence on why this is a requirement, or an ambiguity/assumption.\n"
        "- Ignore chatter, logistics, small talk, jokes and opinions about people, "
        "UNLESS they imply a real requirement for the software.\n"
        "- For background/reference documents, extract only normative statements, "
        "constraints or stated needs; return [] if there are none.\n"
        "Reply with ONLY a JSON array of objects with keys text, quote, note."
    )
    user = (
        f"Document id: {item['doc_id']} (chunk {item['chunk_id']})\n"
        f"Path: {item['path']}\n"
        f"Title: {item['title']}\n"
        f"Type: {item['kind']}\n\n"
        f"----- DOCUMENT TEXT -----\n{item['text']}\n----- END -----"
    )
    default: list = []
    try:
        raw = chat_json("extract", system, user, item.get("model") or DEFAULT_MODELS["extract"], default)
    except Exception as exc:
        return {
            "raw_candidates": [],
            "extract_notes": [{"chunk_id": item["chunk_id"], "error": f"{type(exc).__name__}: {exc}"}],
        }
    candidates = []
    for entry in _as_list(raw):
        if not isinstance(entry, dict):
            continue
        text = _clean_str(entry.get("text"), 400)
        if not text:
            continue
        candidates.append({
            "doc_id": item["doc_id"],
            "chunk_id": item["chunk_id"],
            "text": text,
            "quote": _clean_str(entry.get("quote"), 300),
            "note": _clean_str(entry.get("note"), 300),
        })
    return {
        "raw_candidates": candidates,
        "extract_notes": [{"chunk_id": item["chunk_id"], "extracted": len(candidates)}],
    }


def _chunk_sort_key(chunk_id: str) -> tuple:
    match = re.match(r"^(D\d+)(?:\.c(\d+))?$", chunk_id)
    if not match:
        return (chunk_id, 0)
    return (match.group(1), int(match.group(2) or 1))


def merge_candidates_node(state: State) -> dict:
    raw = sorted(
        state.get("raw_candidates", []),
        key=lambda c: (
            _chunk_sort_key(c["chunk_id"]),
            re.sub(r"[^a-z0-9]+", " ", c["text"].lower()).strip(),
        ),
    )
    seen: dict[str, dict] = {}
    for cand in raw:
        key = re.sub(r"[^a-z0-9]+", " ", cand["text"].lower()).strip()
        if key not in seen:
            seen[key] = cand
    merged = []
    for idx, cand in enumerate(seen.values(), start=1):
        entry = dict(cand)
        entry["ref"] = f"C{idx:04d}"
        merged.append(entry)
    log(f"merge_candidates: {len(state.get('raw_candidates', []))} raw -> {len(merged)} unique")
    return {"candidates": merged}


def _format_manifest(docs: list) -> str:
    return "\n".join(
        f"{d['id']}: {d['title']} ({d['path']}, {d['kind']}, {d['chars']} chars)"
        for d in docs
    )


def make_batches_node(state: State) -> dict:
    batches = []
    candidates = state.get("candidates", [])
    for idx in range(0, len(candidates), BATCH_SIZE):
        batch_id = f"B{len(batches) + 1:02d}"
        batches.append({"batch_id": batch_id, "candidates": candidates[idx:idx + BATCH_SIZE]})
    log(f"make_batches: {len(candidates)} candidates -> {len(batches)} batches")
    return {"batches": batches}


def fan_out_batches(state: State):
    model = state.get("models", DEFAULT_MODELS)["consolidate"]
    return [Send("consolidate_batch", {**batch, "model": model}) for batch in state.get("batches", [])]


SUB_CONSOLIDATE_SYSTEM = """You are a requirements analyst consolidating ONE BATCH of candidate requirements extracted from a corpus about a library management system (ILS).
Your scope is ONLY this batch. A later global pass will merge your output with other batches.

Rules:
1. Merge candidates in this batch that ask for the same capability (rewording, synonyms, partial overlaps). Prefer fewer, well-scoped requirements over many overlapping ones.
2. Every candidate ref C#### in the batch MUST be covered exactly once - either by a requirement's sources[].cands or by a blacklist entry's cands. Do NOT drop any ref.
3. Do NOT assign ids. Requirement fields: 'name' (<= 8 words), 'area' (short theme label), 'explanation' (2-4 plain-text sentences, no markdown), 'priority' (P1/P2/P3/P4; P1 only for critical/mandatory, P4 for backlog), 'keywords' (3-6 lowercase terms), 'sources': [{doc_id, quote, cands}] with doc_id from the candidate's own doc_id and a short verbatim quote (reuse the candidate's evidence quote).
4. Blacklist: nonsensical, off-topic chatter, or duplicates superseded by a merged requirement -> 'blacklist': [{name, category (conflicting|nonsensical|irrelevant|superseded|other), reason, doc_id, quote, cands}].
5. Collect recurring domain terms into 'glossary': [{term, definition}].

Reply with ONLY a JSON object:
{"requirements": [{"name":..., "area":..., "explanation":..., "priority":"P1|P2|P3|P4", "keywords":[...], "sources":[{"doc_id":"D01","quote":"...","cands":["C0001"]}]}],
 "blacklist": [{"name":..., "category":..., "reason":..., "doc_id":"D01","quote":"...","cands":["C0002"]}],
 "glossary": [{"term":..., "definition":...}]}"""


def consolidate_batch_node(item: dict) -> dict:
    batch_id = item["batch_id"]
    model = item.get("model") or DEFAULT_MODELS["consolidate"]
    lines = []
    for cand in item["candidates"]:
        lines.append(
            f"{cand['ref']} (doc {cand['doc_id']}): {cand['text']}\n"
            f"    evidence: \"{cand['quote']}\""
        )
    user = f"Batch {batch_id} - candidate requirements:\n" + "\n".join(lines)
    default = {"requirements": [], "blacklist": [], "glossary": []}
    result = chat_json(f"consolidate_batch[{batch_id}]", SUB_CONSOLIDATE_SYSTEM, user, model, default)
    if not isinstance(result, dict):
        result = default
    requirements = [r for r in _as_list(result.get("requirements")) if isinstance(r, dict)]
    blacklist = [b for b in _as_list(result.get("blacklist")) if isinstance(b, dict)]
    glossary = [g for g in _as_list(result.get("glossary")) if isinstance(g, dict)]
    log(f"  batch {batch_id}: {len(requirements)} draft reqs, {len(blacklist)} blacklisted")
    return {"batch_drafts_raw": [{"batch_id": batch_id, "requirements": requirements,
                                  "blacklist": blacklist, "glossary": glossary}]}


def merge_batches_node(state: State) -> dict:
    drafts = sorted(state.get("batch_drafts_raw", []), key=lambda d: d.get("batch_id", ""))
    total_reqs = sum(len(_as_list(d.get("requirements"))) for d in drafts)
    total_bl = sum(len(_as_list(d.get("blacklist"))) for d in drafts)
    log(f"merge_batches: {len(drafts)} batch drafts, {total_reqs} draft reqs, {total_bl} blacklisted")
    return {"batch_drafts": drafts}


CONSOLIDATE_SYSTEM = """You are the chief requirements engineer producing the FINAL consolidated requirements specification (as JSON) from BATCH-LEVEL DRAFTS produced by parallel sub-consolidators over one corpus.

You receive: the corpus manifest, the batch drafts (each batch has draft requirements and blacklist entries; every candidate ref C#### is covered somewhere in the drafts), and optionally your previous final draft plus reviewer issues to fix.

Rules (each maps to an output spec):
1. DEDUPLICATION (critical - the QA reviewer rejects overlapping requirements): merge draft requirements ACROSS batches ONLY when they demand the SAME capability in different words. One requirement = ONE capability. Related capabilities (e.g. authentication vs. role management vs. report scheduling) stay SEPARATE requirements even if they belong to the same area. A merged requirement accumulates the sources (doc_id, quote, cands) of everything it absorbs. HARD LIMIT: a requirement must absorb at most 10 candidate refs; if a merged group would exceed this, split it into several atomic requirements instead. Expect roughly 60-120 final requirements for a corpus of this size; producing only 30-40 broad requirements is a FAILURE mode.
2. Do NOT assign ids; the pipeline assigns them. No 'id' field.
3. CONTENT: 'name' (<= 8 words), 'area' (short theme label - unify similar areas across batches), 'explanation' (a paragraph of 2-4 plain-text sentences: what the system must do, for whom, key conditions; NO markdown), 'priority' (exactly P1/P2/P3/P4), 'keywords' (3-6 lowercase terms), 'sources': [{doc_id, quote, cands}].
4. PRIORITY SCALE: P1 Must (critical/core/audit-blocking), P2 Should (important daily workflow), P3 Could (valuable enhancement), P4 Later (backlog). Use P1 sparingly.
5. TRACING: doc_id ONLY from the manifest; every source keeps the cands refs of the draft requirements it absorbed. NO candidate ref may be lost: every C#### that appeared in any batch draft must appear in exactly one final requirement's sources[].cands or in exactly one blacklist entry's cands.
6. BLACKLIST: keep and unify the batches' blacklist entries (dedupe them too); objects {name, category (conflicting|nonsensical|irrelevant|superseded|other), reason, doc_id, quote, cands}. When requirements from different batches conflict, keep the best-supported one (reconcile if possible) and blacklist the rejected variant as 'conflicting' or 'superseded'.
7. CONSISTENCY: one term per concept across the whole specification; produce a single unified 'glossary': [{term, definition}].
8. GROUNDING: do not invent features not present in the drafts.
9. If a previous final draft and issues to fix are provided, produce a FULL revised specification resolving every issue. When the reviewer flags two requirements as duplicates, merge them ONLY if they truly demand the same capability; if they merely share an area, keep both but sharpen each explanation so the boundary is explicit. When a doc's candidates are reported uncovered, make sure at least one requirement cites that doc_id (or blacklist its candidates with a reason).
10. AREA VOCABULARY: use lower-case short area labels and reuse the SAME label for related requirements; do not create near-duplicate labels such as 'report security' vs 'security reporting'.
11. EVIDENCE QUOTES: copy 'quote' verbatim from the draft source (the pipeline verifies it against the corpus later); never paraphrase or invent evidence.
12. NEVER create requirements about the extraction/consolidation process itself (e.g. 'unmapped candidate disposition'). Every requirement must be a software capability grounded in a source. If a candidate cannot be mapped, blacklist it with its real doc_id/quote and a reason.

Reply with ONLY a JSON object:
{"system_summary": "<1-3 sentences: what system do these requirements describe>",
 "requirements": [{"name":..., "area":..., "explanation":..., "priority":"P1|P2|P3|P4", "keywords":[...], "sources":[{"doc_id":"D01","quote":"...","cands":["C0001"]}]}],
 "blacklist": [{"name":..., "category":..., "reason":..., "doc_id":"D01","quote":"...","cands":["C0002"]}],
 "glossary": [{"term":..., "definition":...}]}"""


def consolidate_node(state: State) -> dict:
    model = state.get("models", DEFAULT_MODELS)["consolidate"]
    slim_drafts = []
    for draft in state.get("batch_drafts", []):
        reqs = []
        for r in _as_list(draft.get("requirements")):
            if not isinstance(r, dict):
                continue
            reqs.append({
                "name": _clean_str(r.get("name"), 120),
                "area": _clean_str(r.get("area"), 60),
                "explanation": _clean_str(r.get("explanation"), 350),
                "priority": _clean_str(r.get("priority")),
                "keywords": [_clean_str(k) for k in _as_list(r.get("keywords"))][:6],
                "sources": [
                    {"doc_id": _clean_str(s.get("doc_id")),
                     "quote": _clean_str(s.get("quote"), 160),
                     "cands": [_clean_str(c) for c in _as_list(s.get("cands"))]}
                    for s in _as_list(r.get("sources")) if isinstance(s, dict)
                ],
            })
        bl = [
            {"name": _clean_str(b.get("name"), 160),
             "category": _clean_str(b.get("category")),
             "reason": _clean_str(b.get("reason"), 400),
             "doc_id": _clean_str(b.get("doc_id")),
             "quote": _clean_str(b.get("quote"), 300),
             "cands": [_clean_str(c) for c in _as_list(b.get("cands"))]}
            for b in _as_list(draft.get("blacklist")) if isinstance(b, dict)
        ]
        slim_drafts.append({"batch_id": draft.get("batch_id", ""), "requirements": reqs, "blacklist": bl})
    glossary_pool = []
    for draft in state.get("batch_drafts", []):
        glossary_pool.extend(g for g in _as_list(draft.get("glossary")) if isinstance(g, dict))
    user = (
        f"Corpus manifest:\n{_format_manifest(state['docs'])}\n\n"
        f"Batch drafts (JSON):\n{json.dumps(slim_drafts, ensure_ascii=False, separators=(",", ":"))}\n\n"
        f"Glossary candidates from batches (JSON):\n{json.dumps(glossary_pool, ensure_ascii=False)}\n"
    )
    if state.get("system_summary"):
        user += f"\nPrevious system summary: {state['system_summary']}\n"
    if state.get("requirements"):
        prev = [
            {"name": r["name"], "area": r.get("area", ""), "explanation": r["explanation"][:600],
             "priority": r["priority"], "keywords": r.get("keywords", []),
             "sources": r.get("sources", [])}
            for r in state["requirements"]
        ]
        user += f"\nPrevious final draft requirements:\n{json.dumps(prev, ensure_ascii=False, separators=(",", ":"))}\n"
    if state.get("blacklist"):
        user += f"\nPrevious blacklist:\n{json.dumps(state['blacklist'], ensure_ascii=False, separators=(",", ":"))}\n"
    if state.get("glossary"):
        user += f"\nPrevious glossary:\n{json.dumps(state['glossary'], ensure_ascii=False, separators=(",", ":"))}\n"
    issues = _merge_issues(
        state.get("validate_issues"),
        state.get("adjudicate_issues"),
        state.get("audit_issues"),
        state.get("review_issues"),
    )
    if issues:
        user += "\nISSUES TO FIX (each must be resolved in this revision):\n"
        user += "\n".join(f"- [{i.get('kind')}] {i.get('detail')}" for i in issues[:40])
        user += "\n"
    if state.get("uncovered_refs"):
        user += ("\nUNCOVERED CANDIDATE REFS - these must be covered by the revised "
                 f"requirements or blacklist: {', '.join(state['uncovered_refs'][:60])}\n")
    user += "\nProduce the FINAL consolidated specification JSON now."
    default = {"system_summary": "", "requirements": [], "blacklist": [], "glossary": []}
    result = chat_json("consolidate", CONSOLIDATE_SYSTEM, user, model, default)
    if not isinstance(result, dict):
        result = default
    requirements = [r for r in _as_list(result.get("requirements")) if isinstance(r, dict)]
    blacklist = [b for b in _as_list(result.get("blacklist")) if isinstance(b, dict)]
    glossary = [g for g in _as_list(result.get("glossary")) if isinstance(g, dict)]
    log(f"consolidate: {len(requirements)} requirements, {len(blacklist)} blacklisted, "
        f"{len(glossary)} glossary terms")
    return {
        "system_summary": _clean_str(result.get("system_summary"), 600),
        "requirements": requirements,
        "blacklist": blacklist,
        "glossary": glossary,
    }


def validate_node(state: State) -> dict:
    known_docs = {d["id"] for d in state["docs"]}
    ref_index = _candidate_index(state)
    doc_texts = _doc_texts(state)
    reqs: list[dict] = []
    dropped: list[dict] = []

    for idx, req in enumerate(state.get("requirements", []), start=1):
        name = _clean_str(req.get("name"), 120)
        explanation = _clean_str(req.get("explanation"))
        if not explanation:
            dropped.append({
                "name": name or "Untitled draft requirement",
                "category": "other",
                "reason": "Discarded by deterministic validation: the draft requirement had no "
                          "explanation paragraph.",
                "doc_id": "",
                "quote": "",
                "cands": [],
                "origin": "validation",
            })
            continue
        if not name:
            name = _clean_str(" ".join(explanation.split()[:8]), 120)

        priority = PRIORITY_ALIASES.get(_clean_str(req.get("priority")).lower(), "P3")

        sources = []
        by_doc: dict[str, dict] = {}
        for src in _as_list(req.get("sources")):
            if not isinstance(src, dict):
                continue
            doc_id = _clean_str(src.get("doc_id"))
            if doc_id not in known_docs:
                continue
            cands = [_clean_str(c) for c in _as_list(src.get("cands")) if _clean_str(c)]
            if doc_id in by_doc:
                existing = by_doc[doc_id]
                existing["cands"] = sorted(set(existing["cands"]) | set(cands))
                continue
            by_doc[doc_id] = {
                "doc_id": doc_id,
                "quote": "",
                "cands": cands,
            }
        sources = list(by_doc.values())

        if not sources:
            cands = [
                _clean_str(ref)
                for src in _as_list(req.get("sources")) if isinstance(src, dict)
                for ref in _as_list(src.get("cands"))
                if _clean_str(ref) in ref_index
            ]
            dropped.append({
                "name": name,
                "category": "other",
                "reason": "Discarded by deterministic validation: the consolidator produced this "
                          "statement without any traceable source document, so it cannot be "
                          "grounded in the corpus.",
                "doc_id": "",
                "quote": "",
                "cands": sorted(set(cands)),
                "origin": "validation",
            })
            continue

        area = _clean_str(req.get("area"), 60).lower() or "general"
        keywords = [_clean_str(k).lower() for k in _as_list(req.get("keywords")) if _clean_str(k)]
        entry = {
            "id": f"REQ-{idx:03d}",
            "name": name,
            "area": area,
            "explanation": explanation,
            "priority": priority,
            "keywords": keywords[:8],
            "sources": sources,
        }
        _ground_sources([entry], ref_index, doc_texts)
        reqs.append(entry)

    base_blacklist = list(state.get("blacklist", []))
    valid_ids = {r["id"] for r in reqs}
    covered_req = _refs_in_requirements(reqs)
    blacklist = _sanitize_blacklist(
        base_blacklist + dropped, known_docs, ref_index, doc_texts,
        valid_ids, covered_req,
    )

    seen_terms: set[str] = set()
    glossary = []
    for entry in state.get("glossary", []):
        if not isinstance(entry, dict):
            continue
        term = _clean_str(entry.get("term"), 60)
        definition = _clean_str(entry.get("definition"), 300)
        key = term.lower()
        if key and key not in seen_terms and definition:
            seen_terms.add(key)
            glossary.append({"term": term, "definition": definition})

    reattached, uncovered = _reattach_uncovered(state, reqs, blacklist, ref_index, doc_texts)
    if reattached:
        _ground_sources(reqs, ref_index, doc_texts)
        blacklist = _sanitize_blacklist(
            base_blacklist + dropped, known_docs, ref_index, doc_texts,
            valid_ids, _refs_in_requirements(reqs),
        )

    reqs = _materialize_uncovered(state, reqs, ref_index, doc_texts, uncovered)
    _renumber(reqs)
    valid_ids = {r["id"] for r in reqs}
    _ground_sources(reqs, ref_index, doc_texts)
    blacklist = _sanitize_blacklist(
        base_blacklist + dropped, known_docs, ref_index, doc_texts,
        valid_ids, _refs_in_requirements(reqs),
    )

    covered_req = _refs_in_requirements(reqs)
    covered_bl = _refs_in_blacklist(blacklist)
    all_refs = {c["ref"] for c in state.get("candidates", []) if c.get("ref")}
    uncovered = sorted(all_refs - covered_req - covered_bl)
    issues: list[dict] = []
    for req in reqs:
        ref_count = sum(len(_as_list(s.get("cands"))) for s in req["sources"])
        if ref_count > MAX_REFS_PER_REQ:
            issues.append({
                "kind": "coverage",
                "detail": f"Requirement {req['id']} ('{req['name']}') still absorbs "
                          f"{ref_count} candidate refs; split it into atomic requirements "
                          f"(at most {MAX_REFS_PER_REQ} refs each).",
            })

    docs_with_candidates = {c["doc_id"] for c in state.get("candidates", [])}
    cited_docs = {s["doc_id"] for r in reqs for s in r["sources"]}
    bl_docs = {b["doc_id"] for b in blacklist if b["doc_id"]}
    untraced = sorted(docs_with_candidates - cited_docs - bl_docs)
    issues += _coverage_issues(uncovered, untraced)

    log(f"validate: {len(reqs)} reqs, {len(blacklist)} blacklisted, "
        f"{len(uncovered)} uncovered refs, {len(issues)} actionable issues")
    return {
        "requirements": reqs,
        "blacklist": blacklist,
        "glossary": glossary,
        "validate_issues": issues,
        "audit_issues": [],
        "uncovered_refs": uncovered,
        "untraced_docs": untraced,
    }


ADJUDICATE_SYSTEM = """You are an independent consistency and fairness auditor for a requirements specification (second opinion; you see what the consolidator produced).
Check the draft for:
(a) semantic CONFLICTS between requirements (two requirements demanding incompatible behavior),
(b) DUPLICATE pairs (same capability stated twice),
(c) UNJUSTIFIED blacklist entries (discarded candidates that were actually legitimate requirements) and missing blacklist entries (requirements that are nonsensical or should have been discarded),
(d) priority mis-assignments that contradict the scale (P1 reserved for critical/mandatory, P4 for backlog items).
You may fully REWRITE the blacklist (keep, fix, add or remove entries; categories: conflicting, nonsensical, irrelevant, superseded, other) but you may NOT edit the requirements; instead report problems about them in 'issues' with the requirement id in the detail text.
Blacklist rules (strict):
- A candidate ref may appear in the blacklist only if it is already in the supplied blacklist OR in 'uncovered_candidates'. Never invent refs.
- Use the supplied candidate evidence (doc_id, text, quote); never claim a candidate/document is absent when it is supplied.
- A ref that is already covered by a requirement MUST NOT be blacklisted.
- Preserve the 'origin' field on entries where it is present.
- Reason may reference only requirement ids that exist in 'requirements'.
Reply with ONLY a JSON object:
{"blacklist": [{"id":"BL-...","name":...,"category":...,"reason":...,"doc_id":...,"quote":...,"cands":[...]}],
 "issues": [{"kind":"conflict|duplicate|blacklist|priority|coverage|trace|format","detail":"..."}]}
If everything is fine return an empty issues list (and the unchanged blacklist)."""


def adjudicate_node(state: State) -> dict:
    model = state.get("models", DEFAULT_MODELS)["adjudicate"]
    ref_index = _candidate_index(state)
    uncovered_candidates = [
        {
            "ref": ref,
            "doc_id": ref_index[ref].get("doc_id", ""),
            "text": _clean_str(ref_index[ref].get("text"), 300),
            "quote": _clean_str(ref_index[ref].get("quote"), 300),
        }
        for ref in _as_list(state.get("uncovered_refs"))
        if ref in ref_index
    ]
    payload = {
        "requirements": [
            {"id": r["id"], "name": r["name"], "area": r["area"],
             "explanation": r["explanation"][:400], "priority": r["priority"],
             "sources": [{"doc_id": s["doc_id"]} for s in r["sources"]]}
            for r in state.get("requirements", [])
        ],
        "blacklist": state.get("blacklist", []),
        "uncovered_candidates": uncovered_candidates,
        "issues_from_validation": state.get("validate_issues", []),
    }
    user = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    default = {"blacklist": state.get("blacklist", []), "issues": []}
    result = chat_json("adjudicate", ADJUDICATE_SYSTEM, user, model, default)
    if not isinstance(result, dict):
        result = default
    blacklist = [b for b in _as_list(result.get("blacklist")) if isinstance(b, dict)] \
        or state.get("blacklist", [])
    issues = [i for i in _as_list(result.get("issues")) if isinstance(i, dict)]
    for issue in issues:
        issue.setdefault("kind", "conflict")
        issue["detail"] = _clean_str(issue.get("detail"), 600)
        issue["detail"] = f"[adjudicator] {issue['detail']}"
    log(f"adjudicate: {len(issues)} issues reported, blacklist size {len(blacklist)}")
    return {"blacklist": blacklist, "adjudicate_issues": issues}


def audit_node(state: State) -> dict:
    known_docs = {d["id"] for d in state["docs"]}
    ref_index = _candidate_index(state)
    doc_texts = _doc_texts(state)
    reqs = state.get("requirements", [])
    valid_ids = {r["id"] for r in reqs}

    _ground_sources(reqs, ref_index, doc_texts)
    blacklist = _sanitize_blacklist(
        state.get("blacklist", []), known_docs, ref_index, doc_texts,
        valid_ids, _refs_in_requirements(reqs),
    )
    reattached, uncovered = _reattach_uncovered(
        state, reqs, blacklist, ref_index, doc_texts
    )
    if reattached:
        _ground_sources(reqs, ref_index, doc_texts)
        blacklist = _sanitize_blacklist(
            state.get("blacklist", []), known_docs, ref_index, doc_texts,
            valid_ids, _refs_in_requirements(reqs),
        )

    reqs = _materialize_uncovered(state, reqs, ref_index, doc_texts, uncovered)
    _renumber(reqs)
    valid_ids = {r["id"] for r in reqs}
    _ground_sources(reqs, ref_index, doc_texts)
    blacklist = _sanitize_blacklist(
        state.get("blacklist", []), known_docs, ref_index, doc_texts,
        valid_ids, _refs_in_requirements(reqs),
    )
    covered_req = _refs_in_requirements(reqs)
    covered_bl = _refs_in_blacklist(blacklist)
    all_refs = {c["ref"] for c in state.get("candidates", []) if c.get("ref")}
    uncovered = sorted(all_refs - covered_req - covered_bl)
    issues: list[dict] = []
    for req in reqs:
        ref_count = sum(len(_as_list(s.get("cands"))) for s in req["sources"])
        if ref_count > MAX_REFS_PER_REQ:
            issues.append({
                "kind": "coverage",
                "detail": f"Requirement {req['id']} ('{req['name']}') absorbs "
                          f"{ref_count} candidate refs; split it into atomic requirements "
                          f"(at most {MAX_REFS_PER_REQ} refs each).",
            })

    docs_with_candidates = {c["doc_id"] for c in state.get("candidates", [])}
    cited_docs = {s["doc_id"] for r in reqs for s in r["sources"]}
    bl_docs = {b["doc_id"] for b in blacklist if b["doc_id"]}
    untraced = sorted(docs_with_candidates - cited_docs - bl_docs)
    issues += _coverage_issues(uncovered, untraced)

    log(f"audit: {len(reqs)} reqs, {len(blacklist)} blacklisted, "
        f"{len(uncovered)} uncovered refs, {len(issues)} actionable issues")
    return {
        "blacklist": blacklist,
        "uncovered_refs": uncovered,
        "untraced_docs": untraced,
        "audit_issues": issues,
    }


REVIEW_SYSTEM = """You are the final QA reviewer of a requirements specification produced by an agentic pipeline. You receive the corpus manifest, per-document candidate counts, the current requirements (with tracing), the blacklist and the glossary, plus issues already flagged by deterministic validation.

Verify EVERY output specification and report issues (kind, detail):
- OS2 unique identification: ids unique and well formed.
- OS3 no semantically duplicate requirements (check names AND explanations; report pairs).
- OS4 tracing: every requirement must cite real source documents; flag suspicious tracing (a requirement citing a document whose content plausibly says nothing about it cannot be verified by you - only flag if sources are empty or clearly mismatched with the explanation).
- OS5 quality: name short and descriptive; explanation paragraph-long and informative. Flag thin/empty ones. Also flag 'over-merged' requirements whose candidate_ref_count exceeds 12: they bundle several distinct capabilities and must be split.
- OS6 priority: consistent with the scale (P1 critical ... P4 backlog); flag nonsense priorities.
- OS7 consistency: conflicting requirements or inconsistent vocabulary (flag specific pairs/terms).
- OS8 completeness: documents that produced candidates but appear in NEITHER the requirements NOR the blacklist must be flagged; also flag 'coverage' issues passed from validation.
- OS9 blacklist: every discarded candidate needs a reason; flag missing/weak entries.
Only report REAL problems - do not invent pedantic style nits. At most 25 issues, most severe first.
Reply with ONLY a JSON object:
{"pass": true|false, "notes": "<short overall assessment>", "issues": [{"kind":"duplicate|conflict|trace|format|priority|coverage|blacklist|quality","detail":"..."}]}
'pass' may be true only if there are zero HIGH-severity issues (missing coverage, duplicates, conflicts, missing tracing, missing blacklist reasons)."""


def review_node(state: State) -> dict:
    model = state.get("models", DEFAULT_MODELS)["review"]
    cand_counts: dict[str, int] = {}
    for cand in state.get("candidates", []):
        cand_counts[cand["doc_id"]] = cand_counts.get(cand["doc_id"], 0) + 1
    coverage = []
    for doc in state["docs"]:
        cited = sum(1 for r in state.get("requirements", []) for s in r["sources"] if s["doc_id"] == doc["id"])
        bl = sum(1 for b in state.get("blacklist", []) if b.get("doc_id") == doc["id"])
        coverage.append({
            "doc_id": doc["id"], "title": doc["title"],
            "candidates": cand_counts.get(doc["id"], 0),
            "cited_by_requirements": cited, "blacklist_entries": bl,
        })
    payload = {
        "iteration": state.get("iteration", 0),
        "system_summary": state.get("system_summary", ""),
        "document_coverage": coverage,
        "untraced_docs": state.get("untraced_docs", []),
        "uncovered_candidate_refs": state.get("uncovered_refs", []),
        "requirements": [
            {"id": r["id"], "name": r["name"], "area": r["area"], "priority": r["priority"],
             "explanation": r["explanation"][:600],
             "candidate_ref_count": sum(len(_as_list(s.get("cands"))) for s in r["sources"]),
             "sources": [s["doc_id"] for s in r["sources"]]}
            for r in state.get("requirements", [])
        ],
        "blacklist": [
            {"id": b["id"], "name": b["name"], "category": b["category"], "reason": b["reason"],
             "doc_id": b.get("doc_id", "")}
            for b in state.get("blacklist", [])
        ],
        "glossary": state.get("glossary", []),
        "issues_from_validation_and_adjudication": _merge_issues(
            state.get("validate_issues"),
            state.get("adjudicate_issues"),
            state.get("audit_issues"),
        ),
    }
    user = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    default = {"pass": False, "notes": "reviewer unavailable", "issues": []}
    result = chat_json("review", REVIEW_SYSTEM, user, model, default)
    if not isinstance(result, dict):
        result = default
    passed = bool(result.get("pass"))
    issues = [i for i in _as_list(result.get("issues")) if isinstance(i, dict)]
    for issue in issues:
        issue.setdefault("kind", "quality")
        issue["detail"] = f"[reviewer] {_clean_str(issue.get('detail'), 600)}"
    iteration = state.get("iteration", 0) + 1
    entry = {
        "iteration": iteration,
        "pass": passed,
        "issue_count": len(issues),
        "kinds": sorted({i["kind"] for i in issues}),
        "notes": _clean_str(result.get("notes"), 500),
    }
    log(f"review (pass {iteration}): pass={passed}, {len(issues)} issues")
    return {
        "review_pass": passed,
        "review_issues": issues,
        "review_log": _as_list(state.get("review_log")) + [entry],
        "iteration": iteration,
    }


def route_after_review(state: State) -> str:
    if state.get("review_pass") or state.get("iteration", 0) >= state.get("max_iterations", 3):
        return "render"
    return "consolidate"


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_node(state: State) -> dict:
    docs = state["docs"]
    reqs = state["requirements"]
    blacklist = state["blacklist"]
    lines: list[str] = []
    lines.append("# Software Requirements Specification")
    lines.append("")
    summary = state.get("system_summary") or "Requirements refined from the provided document corpus."
    lines.append(f"*System under specification:* {summary}")
    lines.append("")
    lines.append(f"*Generated:* {utc_now()} by a LangGraph agentic network "
                 f"(extraction: {state['models']['extract']}, consolidation: "
                 f"{state['models']['consolidate']}, adjudication: {state['models']['adjudicate']}, "
                 f"review: {state['models']['review']})")
    lines.append(f"*Source corpus:* {len(docs)} documents")
    lines.append("")
    lines.append("## 1. Priority scale")
    lines.append("")
    lines.append("| Priority | Meaning |")
    lines.append("|---|---|")
    for code, meaning in PRIORITY_SCALE.items():
        lines.append(f"| **{code}** | {meaning} |")
    lines.append("")
    lines.append("## 2. Glossary (consistent terminology)")
    lines.append("")
    if state.get("glossary"):
        lines.append("| Term | Definition |")
        lines.append("|---|---|")
        for g in state["glossary"]:
            lines.append(f"| {_md_escape(g['term'])} | {_md_escape(g['definition'])} |")
    else:
        lines.append("_No glossary entries were produced._")
    lines.append("")
    lines.append("## 3. Requirements overview")
    lines.append("")
    lines.append("| ID | Name | Priority | Area | Sources |")
    lines.append("|---|---|---|---|---|")
    for r in reqs:
        srcs = ", ".join(sorted({s["doc_id"] for s in r["sources"]})) or "—"
        lines.append(f"| {r['id']} | {_md_escape(r['name'])} | {r['priority']} | "
                     f"{_md_escape(r['area'])} | {srcs} |")
    lines.append("")
    lines.append("## 4. Requirements")
    lines.append("")
    ordered_reqs = sorted(reqs, key=lambda r: (r["area"].lower(), r["id"]))
    for area, area_reqs in groupby(ordered_reqs, key=lambda r: r["area"]):
        lines.append(f"### Area: {area}")
        lines.append("")
        for r in area_reqs:
            lines.append(f"#### {r['id']}: {r['name']}")
            lines.append("")
            lines.append(f"**Priority:** {r['priority']} — {PRIORITY_SCALE[r['priority']]}")
            lines.append("")
            lines.append(r["explanation"])
            lines.append("")
            if r["sources"]:
                lines.append("**Sources:**")
                lines.append("")
                for s in r["sources"]:
                    title = next((d["title"] for d in docs if d["id"] == s["doc_id"]), s["doc_id"])
                    quote = f" — \"{s['quote']}\"" if s["quote"] else ""
                    lines.append(f"- `{s['doc_id']}` {title}{quote}")
            else:
                lines.append("**Sources:** _none recorded_")
            if r["keywords"]:
                lines.append("")
                lines.append("**Keywords:** " + ", ".join(r["keywords"]))
            lines.append("")
    lines.append("## 5. Blacklist (discarded candidates)")
    lines.append("")
    lines.append("Candidates that were identified but deliberately discarded, with the reason "
                 "for each rejection:")
    lines.append("")
    if blacklist:
        lines.append("| ID | Candidate | Category | Reason | Source |")
        lines.append("|---|---|---|---|---|")
        for b in blacklist:
            src = b["doc_id"] or "—"
            lines.append(f"| {b['id']} | {_md_escape(b['name'])} | {b['category']} | "
                         f"{_md_escape(b['reason'])} | {src} |")
    else:
        lines.append("_No candidates were discarded._")
    lines.append("")
    lines.append("## 6. Coverage appendix (document → requirements)")
    lines.append("")
    lines.append("| Doc | Document | Candidates | Requirements citing it | Blacklist entries |")
    lines.append("|---|---|---|---|---|")
    cand_counts: dict[str, int] = {}
    for cand in state.get("candidates", []):
        cand_counts[cand["doc_id"]] = cand_counts.get(cand["doc_id"], 0) + 1
    for d in docs:
        cited = sum(1 for r in reqs for s in r["sources"] if s["doc_id"] == d["id"])
        bl = sum(1 for b in blacklist if b.get("doc_id") == d["id"])
        lines.append(f"| {d['id']} | {_md_escape(d['title'])} ({d['path']}) | "
                     f"{cand_counts.get(d['id'], 0)} | {cited} | {bl} |")
    lines.append("")
    lines.append("## 7. Review log")
    lines.append("")
    lines.append("| Iteration | Passed | Issues | Kinds | Notes |")
    lines.append("|---|---|---|---|---|")
    for entry in state.get("review_log", []):
        lines.append(f"| {entry['iteration']} | {'yes' if entry['pass'] else 'no'} | "
                     f"{entry['issue_count']} | {_md_escape(', '.join(entry['kinds']))} | "
                     f"{_md_escape(entry['notes'])} |")
    lines.append("")
    final_pass = "yes" if state.get("review_pass") else \
        "no (iteration budget exhausted - see review log)"
    lines.append(f"*Final QA verdict:* {final_pass}")
    lines.append("")
    uncovered = len(state.get("uncovered_refs") or [])
    advisory = len(state.get("audit_issues") or [])
    lines.append(
        f"*Post-review deterministic audit:* {uncovered} uncovered candidate refs, "
        f"{len(blacklist)} blacklist entries; {advisory} advisory coverage issue(s)."
    )
    lines.append("")
    md = "\n".join(lines)
    log(f"render: {len(reqs)} requirements, {len(blacklist)} blacklist entries, {len(md)} chars")
    return {"rendered_md": md}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("ingest", ingest_node)
    builder.add_node("extract", extract_node)
    builder.add_node("merge_candidates", merge_candidates_node)
    builder.add_node("make_batches", make_batches_node)
    builder.add_node("consolidate_batch", consolidate_batch_node)
    builder.add_node("merge_batches", merge_batches_node)
    builder.add_node("consolidate", consolidate_node)
    builder.add_node("validate", validate_node)
    builder.add_node("adjudicate", adjudicate_node)
    builder.add_node("audit", audit_node)
    builder.add_node("review", review_node)
    builder.add_node("render", render_node)
    builder.add_edge(START, "ingest")
    builder.add_conditional_edges("ingest", fan_out, ["extract"])
    builder.add_edge("extract", "merge_candidates")
    builder.add_edge("merge_candidates", "make_batches")
    builder.add_conditional_edges("make_batches", fan_out_batches, ["consolidate_batch"])
    builder.add_edge("consolidate_batch", "merge_batches")
    builder.add_edge("merge_batches", "consolidate")
    builder.add_edge("consolidate", "validate")
    builder.add_edge("validate", "adjudicate")
    builder.add_edge("adjudicate", "audit")
    builder.add_edge("audit", "review")
    builder.add_conditional_edges("review", route_after_review, ["consolidate", "render"])
    builder.add_edge("render", END)
    return builder.compile()


def _write_outputs(final: dict, output_dir: Path, elapsed: float | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "requirements.md"
    md_path.write_text(final.get("rendered_md", ""), encoding="utf-8")
    state_path = output_dir / "state.json"
    dump = {k: v for k, v in final.items() if k != "work_items"}
    dump["work_items"] = [
        {**w, "text": w["text"][:500] + ("…" if len(w["text"]) > 500 else "")}
        for w in final.get("work_items", [])
    ]
    if elapsed is not None:
        dump["wall_seconds"] = round(elapsed, 1)
    state_path.write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"wrote {md_path}")
    log(f"wrote {state_path}")


def run_offline_audit(state_path: Path, output_dir: Path, input_override: str | None) -> int:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    input_dir = Path(input_override or state.get("input_dir") or (BASE_DIR / "data" / "corpus")).resolve()
    docs, items = load_corpus(input_dir)
    state["input_dir"] = str(input_dir)
    state["docs"] = docs
    state["work_items"] = [vars(item) for item in items]
    state.setdefault("models", DEFAULT_MODELS)
    state.setdefault("review_log", [])
    state.setdefault("iteration", 0)
    state.setdefault("review_pass", False)
    log(f"offline audit: {len(docs)} documents, {len(state.get('requirements', []))} draft requirements")

    state.update(validate_node(state))
    state.update(audit_node(state))
    state.update(render_node(state))
    _write_outputs(state, output_dir)
    log(f"offline audit done: {len(state.get('requirements', []))} requirements, "
        f"{len(state.get('blacklist', []))} blacklist entries")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Agentic network for requirements refinement")
    parser.add_argument("--input", default=str(BASE_DIR / "data" / "corpus"),
                        help="directory with the input corpus (any path)")
    parser.add_argument("--output", default=str(BASE_DIR / "output"),
                        help="directory for requirements.md and state.json")
    parser.add_argument("--max-iterations", type=int, default=3,
                        help="max review->consolidate loop iterations")
    parser.add_argument("--model-extract", default=DEFAULT_MODELS["extract"])
    parser.add_argument("--model-consolidate", default=DEFAULT_MODELS["consolidate"])
    parser.add_argument("--model-adjudicate", default=DEFAULT_MODELS["adjudicate"])
    parser.add_argument("--model-review", default=DEFAULT_MODELS["review"])
    parser.add_argument("--dry-run", action="store_true",
                        help="run only the deterministic ingest and print the manifest")
    parser.add_argument("--audit-state", default=None,
                        help="re-run the deterministic validate/audit/render stages on an existing state.json")
    args = parser.parse_args()

    load_dotenv(BASE_DIR / ".env")
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    if args.audit_state:
        return run_offline_audit(Path(args.audit_state).resolve(), output_dir, args.input)

    if args.dry_run:
        docs, items = load_corpus(input_dir)
        for d in docs:
            print(f"{d['id']} {d['kind']:5} {d['chars']:6} ch={d['chunks']}  {d['path']}  {d['title']}")
        print(f"{len(docs)} documents, {len(items)} work items")
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set (env var or Task_1/.env)", file=sys.stderr)
        return 1

    models = {
        "extract": args.model_extract,
        "consolidate": args.model_consolidate,
        "adjudicate": args.model_adjudicate,
        "review": args.model_review,
    }
    log(f"models: {models}")
    log(f"input: {input_dir}")
    graph = build_graph()
    initial: State = {
        "input_dir": str(input_dir),
        "max_iterations": args.max_iterations,
        "models": models,
        "iteration": 0,
        "review_log": [],
    }
    started = time.perf_counter()
    final = graph.invoke(initial, config={"recursion_limit": 200})
    elapsed = time.perf_counter() - started
    log(f"graph finished in {elapsed:.1f}s")

    _write_outputs(final, output_dir, elapsed)
    log(f"final review pass: {final.get('review_pass')} "
        f"after {final.get('iteration')} iteration(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
