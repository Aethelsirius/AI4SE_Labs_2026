"""Task 4 significance: are the prompt gaps luck or real?

Paired fair-coin check per prompt pair (exact McNemar test): if both
prompts were equally good, each question they disagree on is a coin
flip. Reports how often a fair coin produces a split this lopsided,
with Holm correction over the 3 pairs (alpha 0.05).
"""
# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false

import csv
import dataclasses
import itertools
import json
import math
from pathlib import Path

T4 = Path(__file__).resolve().parent
T2 = T4.parent / "Task_2"
T3 = T4.parent / "Task_3"
FIGS = T4 / "figs"
PROMPTS = ["rtf", "fewshot", "cot"]
NAMES = {"rtf": "RTF", "fewshot": "Few-Shot", "cot": "CoT"}
COLORS = {"rtf": "#0072B2", "fewshot": "#E69F00", "cot": "#009E73"}
ALPHA = 0.05


@dataclasses.dataclass
class Pair:
    a: str
    b: str
    a_only: int
    b_only: int
    p_raw: float
    p_holm: float = 1.0
    significant: bool = False


def fair_coin_p(a_only: int, b_only: int) -> float:
    """Two-sided exact probability of a split this lopsided (or worse)."""
    n = a_only + b_only
    if n == 0:
        return 1.0
    lo = min(a_only, b_only)
    one_sided = sum(math.comb(n, k) for k in range(lo + 1)) / 2**n
    return min(1.0, 2 * one_sided)


def one_in(p: float) -> str:
    if p >= 1.0:
        return "1 in 1 (certain)"
    if p <= 0.0:
        return "1 in >10^15"
    inv = 1 / p
    if inv >= 1_000_000_000:
        return f"1 in {inv:.0e}".replace("e+0", "e")
    if inv >= 1000:
        return f"1 in {inv:,.0f}"
    return f"1 in {inv:.1f}"


def grouped_bars(path: Path, title: str, ylabel: str, groups: list[str],
                 left: list[float], right: list[float],
                 left_colors: list[str], right_colors: list[str]) -> None:
    w, h, pad_l, pad_b, pad_t = 560, 320, 56, 64, 44
    n = len(groups)
    slot = (w - pad_l - 20) / n
    bw = min(70, slot * 0.28)
    vmax = 70
    scale = h - pad_t - pad_b

    def y(v: float) -> float:
        return pad_t + scale * (1 - v / vmax)

    head = (
        "<svg xmlns='http://www.w3.org/2000/svg' "
        f"width='{w}' height='{h}' role='img'>"
    )
    title_el = (
        f"<text x='{w // 2}' y='22' text-anchor='middle' font-size='15' "
        f"font-family='sans-serif'>{title}</text>"
    )
    sub = (
        "<text x='240' y='40' text-anchor='middle' font-size='11' "
        "font-family='sans-serif'>left bar = first-named prompt only, "
        "right bar = second-named prompt only</text>"
    )
    axis = (
        f"<text x='14' y='{h // 2}' text-anchor='middle' font-size='11' "
        f"font-family='sans-serif' transform='rotate(-90 14 {h // 2})'>{ylabel}</text>"
    )
    s = [head, title_el, sub, axis]
    for i in range(0, 71, 10):
        yy = y(float(i))
        s.append(f"<line x1='{pad_l}' y1='{yy:.1f}' x2='{w - 10}' y2='{yy:.1f}' stroke='#ddd'/>")
        s.append(f"<text x='{pad_l - 6}' y='{yy + 4:.1f}' text-anchor='end' font-size='10' font-family='sans-serif'>{i}</text>")
    for i, g in enumerate(groups):
        cx = pad_l + slot * i + slot / 2
        for j, (v, c) in enumerate(((left[i], left_colors[i]), (right[i], right_colors[i]))):
            x = cx + (j - 0.5) * (bw + 6) - bw / 2
            s.append(f"<rect x='{x:.1f}' y='{y(v):.1f}' width='{bw:.1f}' height='{h - pad_b - y(v):.1f}' fill='{c}'/>")
            s.append(f"<text x='{x + bw / 2:.1f}' y='{y(v) - 6:.1f}' text-anchor='middle' font-size='11' font-family='sans-serif'>{v:.0f}</text>")
        s.append(f"<text x='{cx:.1f}' y='{h - pad_b + 20}' text-anchor='middle' font-size='12' font-family='sans-serif'>{g}</text>")
    s.append(f"<line x1='{pad_l}' y1='{pad_t}' x2='{pad_l}' y2='{h - pad_b}' stroke='#333'/>")
    s.append(f"<line x1='{pad_l}' y1='{h - pad_b}' x2='{w - 10}' y2='{h - pad_b}' stroke='#333'/>")
    s.append("</svg>")
    _ = path.write_text("\n".join(s))


def main() -> None:
    _ = csv.field_size_limit(10**9)
    verdict: dict[str, dict[str, int]] = {}
    for name in PROMPTS:
        with (T2 / f"results_{name}.csv").open(newline="") as f:
            verdict[name] = {r["id"]: int(r["correct"]) for r in csv.DictReader(f)}
    ids = list(next(iter(verdict.values())).keys())
    assert all(set(v) == set(ids) for v in verdict.values())

    pairs = list(itertools.combinations(PROMPTS, 2))
    rows: list[Pair] = []
    for a, b in pairs:
        a_only = sum(1 for i in ids if verdict[a][i] == 1 and verdict[b][i] == 0)
        b_only = sum(1 for i in ids if verdict[b][i] == 1 and verdict[a][i] == 0)
        rows.append(Pair(a=a, b=b, a_only=a_only, b_only=b_only,
                         p_raw=fair_coin_p(a_only, b_only)))
    # Holm correction over the 3 pairs.
    order = sorted(range(len(rows)), key=lambda k: rows[k].p_raw)
    last = 0.0
    for rank, k in enumerate(order):
        last = max(last, min(1.0, (len(rows) - rank) * rows[k].p_raw))
        rows[k].p_holm = last
        rows[k].significant = last < ALPHA

    _ = (T4 / "statistics.json").write_text(json.dumps(
        {"alpha": ALPHA, "method": "exact McNemar (fair-coin) + Holm",
         "pairs": [dataclasses.asdict(r) for r in rows]}, indent=2))

    FIGS.mkdir(exist_ok=True)
    groups = [f"{NAMES[r.a]} vs {NAMES[r.b]}" for r in rows]
    grouped_bars(
        FIGS / "discordant.svg", "Questions only one prompt got right",
        "questions", groups,
        [float(r.a_only) for r in rows], [float(r.b_only) for r in rows],
        [COLORS[r.a] for r in rows], [COLORS[r.b] for r in rows],
    )

    print("| pair | only-A | only-B | chance | significant |")
    print("|---|---|---|---|---|")
    for r in rows:
        tag = f"{NAMES[r.a]} vs {NAMES[r.b]}"
        verdict_out = "yes" if r.significant else "no"
        line_out = (
            f"| {tag} | {r.a_only} | {r.b_only} | {one_in(r.p_holm)} "
            f"| {verdict_out} |"
        )
        print(line_out)
    print("\nwrote statistics.json, figs/discordant.svg")


if __name__ == "__main__":
    main()
