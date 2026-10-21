from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

REQ_HEADER_RE = re.compile(r"^#### (REQ-\d{3}): (.+)$", re.M)
REQ_BLOCK_RE = re.compile(r"^#### (REQ-\d{3}): (.+?)\n(.*?)(?=^#### |^### Area|^\Z)", re.M | re.S)
SOURCE_RE = re.compile(r"^- `(D\d{2})`", re.M)
DOC_ROW_RE = re.compile(r"^\| (D\d{2}) \|", re.M)
BLACKLIST_ROW_RE = re.compile(r"^\| (BL-\d{3}) \|", re.M)
AREA_RE = re.compile(r"^### Area: (.+)$", re.M)
PRIORITY_RE = re.compile(r"\*\*Priority:\*\* (P[1-4])")

NAME_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "report",
    "reporting", "system", "support", "management", "based", "data",
}


def _name_terms(name: str) -> set[str]:
    tokens: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", name.lower()):
        if len(token) < 3 or token in NAME_STOPWORDS:
            continue
        if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
            token = token[:-1]
        tokens.add(token)
    return tokens


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _doc_texts(state: dict) -> dict[str, str]:
    base = Path(state.get("input_dir") or (BASE_DIR / "data" / "corpus"))
    texts: dict[str, str] = {}
    for doc in state.get("docs", []):
        path = base / doc.get("path", "")
        if path.is_file():
            texts[doc["id"]] = _normalize_text(
                path.read_text(encoding="utf-8", errors="replace")
            )
    return texts


def check_markdown(md: str) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    headers = REQ_HEADER_RE.findall(md)
    ids = [h[0] for h in headers]
    results.append(("OS1 single document with structure",
                    all(s in md for s in ("# Software Requirements Specification", "## 3. Requirements overview", "## 4. Requirements")),
                    "title + overview + requirements sections present"))
    results.append(("OS2 unique requirement ids",
                    len(ids) == len(set(ids)) and len(ids) > 0,
                    f"{len(ids)} ids, {len(set(ids))} unique"))

    names = [h[1].strip().lower() for h in headers]
    dup_names = sorted({n for n in names if names.count(n) > 1})
    results.append(("OS3 no duplicate requirement names",
                    not dup_names,
                    f"{len(dup_names)} duplicated names" + (f": {dup_names[:3]}" if dup_names else "")))

    term_sets = [(h[0], _name_terms(h[1])) for h in headers]
    near_dups = []
    for i, (left_id, left_terms) in enumerate(term_sets):
        if not left_terms:
            continue
        for right_id, right_terms in term_sets[i + 1:]:
            if not right_terms:
                continue
            similarity = len(left_terms & right_terms) / len(left_terms | right_terms)
            if similarity >= 0.8:
                near_dups.append((left_id, right_id, round(similarity, 2)))
    results.append(("OS3 no near-duplicate requirement names",
                    not near_dups,
                    f"{len(near_dups)} near-duplicate pairs" + (f": {near_dups[:3]}" if near_dups else "")))

    doc_rows = set(DOC_ROW_RE.findall(md))
    cited: set[str] = set()
    no_source = []
    for block in REQ_BLOCK_RE.finditer(md):
        rid, _, body = block.group(1), block.group(2), block.group(3)
        srcs = set(SOURCE_RE.findall(body))
        if not srcs:
            no_source.append(rid)
        cited |= srcs
    results.append(("OS4 tracing: every requirement cites corpus documents",
                    not no_source and cited <= doc_rows,
                    f"docs cited: {len(cited)}, untraceable: {no_source[:5] or 'none'}"))

    thin = []
    for block in REQ_BLOCK_RE.finditer(md):
        rid, body = block.group(1), block.group(3)
        prio = PRIORITY_RE.search(body)
        after = body.split("**Sources:**")[0]
        explanation = [ln for ln in after.splitlines()
                       if ln.strip() and not ln.startswith("**") and not ln.startswith("#")]
        words = sum(len(ln.split()) for ln in explanation)
        if not prio or words < 15:
            thin.append(rid)
    results.append(("OS5 name + paragraph explanation per requirement",
                    not thin,
                    f"requirements with thin explanation/missing priority: {thin[:5] or 'none'}"))

    results.append(("OS6 priority scale explained + used",
                    "## 1. Priority scale" in md and "**P1**" in md and "**P4**" in md
                    and all(PRIORITY_RE.search(b.group(3)) for b in REQ_BLOCK_RE.finditer(md)),
                    "scale legend present, all requirements carry P1-P4"))

    glossary_section = ""
    if "## 2. Glossary" in md:
        glossary_section = md.split("## 2. Glossary", 1)[1].split("## 3.", 1)[0]
    glossary_rows = [ln for ln in glossary_section.splitlines()
                     if ln.startswith("| ") and not ln.startswith("| Term") and not ln.startswith("|---")]
    results.append(("OS7 glossary for consistent vocabulary",
                    len(glossary_rows) >= 3,
                    f"{len(glossary_rows)} glossary entries"))

    areas = AREA_RE.findall(md)
    dup_areas = sorted({a for a in areas if areas.count(a) > 1})
    results.append(("OS7 area sections uniquely grouped",
                    bool(areas) and not dup_areas,
                    f"{len(areas)} area headers, {len(set(areas))} unique"
                    + (f", duplicated: {dup_areas[:3]}" if dup_areas else "")))

    results.append(("OS8 coverage appendix lists every document",
                    len(doc_rows) > 0 and "## 6. Coverage appendix" in md,
                    f"{len(doc_rows)} documents in coverage appendix"))

    bl_rows = BLACKLIST_ROW_RE.findall(md)
    bl_weak = [ln for ln in md.splitlines()
               if ln.startswith("| BL-") and ln.count("|") < 6]
    results.append(("OS9 blacklist section with reasons",
                    "## 5. Blacklist" in md and not bl_weak,
                    f"{len(bl_rows)} blacklist entries"
                    + ("" if bl_rows else " (none discarded)")))
    return results


def check_state(state: dict) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    reqs = state.get("requirements", [])
    ids = [r["id"] for r in reqs]
    results.append(("state: unique ids", len(ids) == len(set(ids)), f"{len(ids)} reqs"))
    known = {d["id"] for d in state.get("docs", [])}
    bad_src = [r["id"] for r in reqs
               for s in r.get("sources", []) if s["doc_id"] not in known]
    results.append(("state: sources inside corpus", not bad_src, f"bad: {bad_src[:5] or 'none'}"))
    bad_prio = [r["id"] for r in reqs if r.get("priority") not in ("P1", "P2", "P3", "P4")]
    results.append(("state: valid priorities", not bad_prio, f"bad: {bad_prio[:5] or 'none'}"))
    results.append(("state: zero uncovered candidate refs",
                    not state.get("uncovered_refs"),
                    f"uncovered: {len(state.get('uncovered_refs', []))}"))
    results.append(("state: every corpus document traced",
                    not state.get("untraced_docs"),
                    f"untraced: {state.get('untraced_docs', []) or 'none'}"))

    all_refs = {c.get("ref") for c in state.get("candidates", []) if c.get("ref")}
    req_refs = {
        ref for r in reqs for s in r.get("sources", [])
        for ref in s.get("cands", [])
    }
    bl_refs = {
        ref for b in state.get("blacklist", [])
        for ref in b.get("cands", [])
    }
    bad_bl_refs = sorted(bl_refs - all_refs)
    results.append(("state: blacklist refs are real candidates",
                    not bad_bl_refs,
                    f"bad: {bad_bl_refs[:5] or 'none'}"))
    overlap = sorted(req_refs & bl_refs)
    results.append(("state: candidate refs covered exactly once",
                    not overlap,
                    f"overlap: {overlap[:5] or 'none'}"))

    bad_bl_doc = [
        b["id"] for b in state.get("blacklist", [])
        if b.get("doc_id") and b["doc_id"] not in known
    ]
    results.append(("state: blacklist docs inside corpus",
                    not bad_bl_doc,
                    f"bad: {bad_bl_doc[:5] or 'none'}"))
    bad_reason = [b["id"] for b in state.get("blacklist", []) if not b.get("reason")]
    results.append(("state: blacklist entries have reasons",
                    not bad_reason,
                    f"missing: {bad_reason[:5] or 'none'}"))

    texts = _doc_texts(state)
    if texts:
        bad_quotes = []
        for r in reqs:
            for s in r.get("sources", []):
                quote = _normalize_text(s.get("quote"))
                if quote and quote not in texts.get(s.get("doc_id", ""), ""):
                    bad_quotes.append((r["id"], s.get("doc_id")))
        for b in state.get("blacklist", []):
            quote = _normalize_text(b.get("quote"))
            if quote and quote not in texts.get(b.get("doc_id", ""), ""):
                bad_quotes.append((b["id"], b.get("doc_id")))
        results.append(("state: quotes verbatim in source documents",
                        not bad_quotes,
                        f"non-verbatim: {bad_quotes[:5] or 'none'}"
                        f" ({len(bad_quotes)} total)" if bad_quotes else "all quotes verbatim"))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic OS-spec checker")
    parser.add_argument("--md", default=str(BASE_DIR / "output" / "requirements.md"))
    parser.add_argument("--state", default=str(BASE_DIR / "output" / "state.json"))
    args = parser.parse_args()

    md = Path(args.md).read_text(encoding="utf-8")
    results = check_markdown(md)
    state_path = Path(args.state)
    if state_path.exists():
        results += check_state(json.loads(state_path.read_text(encoding="utf-8")))

    failed = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        failed += 0 if ok else 1
        print(f"[{mark}] {name}: {detail}")
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
