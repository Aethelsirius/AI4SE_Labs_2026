"""Task 3 metric: count calibration of Text-to-SQL predictions.

Per question: err = |actual_count - expected_count| (net row-count
difference from Task_2/results_*.csv; content-blind by design).
Per prompt: count-accuracy over all 155, wrong-median + wrong-mean over
exact-mismatch rows only.
"""
# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false

import csv
import json
from pathlib import Path

T3 = Path(__file__).resolve().parent
T2 = T3.parent / "Task_2"
FIGS = T3 / "figs"
PROMPTS = ["rtf", "fewshot", "cot"]

COLORS = {"rtf": "#0072B2", "fewshot": "#E69F00", "cot": "#009E73"}
NAMES = {"rtf": "RTF", "fewshot": "Few-Shot", "cot": "CoT"}


def nice_ceiling(v: float) -> float:
    if v <= 0:
        return 1.0
    import math
    mag = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= v:
            return m * mag
    return 10 * mag


def bar_chart(path: Path, title: str, ylabel: str, labels: list[str],
              values: list[float], colors: list[str], fmt: str) -> None:
    w, h, pad_l, pad_b, pad_t = 480, 300, 56, 48, 36
    n = len(labels)
    slot = (w - pad_l - 20) / n
    bw = min(90, slot * 0.55)
    vmax = nice_ceiling(max(values)) if values else 1
    scale = h - pad_t - pad_b

    def y(v: float) -> float:
        return pad_t + scale * (1 - v / vmax)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" role="img">',
             f"<text x='{w // 2}' y='22' text-anchor='middle' font-size='15' font-family='sans-serif'>{title}</text>",
             f"<text x='14' y='{h // 2}' text-anchor='middle' font-size='11' font-family='sans-serif' transform='rotate(-90 14 {h // 2})'>{ylabel}</text>"]
    for i in range(5):
        v = vmax * i / 4
        yy = y(v)
        parts.append(f"<line x1='{pad_l}' y1='{yy:.1f}' x2='{w - 10}' y2='{yy:.1f}' stroke='#ddd'/>")
        parts.append(f"<text x='{pad_l - 6}' y='{yy + 4:.1f}' text-anchor='end' font-size='10' font-family='sans-serif'>{fmt.format(v)}</text>")
    for i, (lab, v, c) in enumerate(zip(labels, values, colors)):
        x = pad_l + slot * i + (slot - bw) / 2
        parts.append(f"<rect x='{x:.1f}' y='{y(v):.1f}' width='{bw:.1f}' height='{h - pad_b - y(v):.1f}' fill='{c}'/>")
        parts.append(f"<text x='{x + bw / 2:.1f}' y='{y(v) - 6:.1f}' text-anchor='middle' font-size='11' font-family='sans-serif'>{fmt.format(v)}</text>")
        parts.append(f"<text x='{x + bw / 2:.1f}' y='{h - pad_b + 20}' text-anchor='middle' font-size='12' font-family='sans-serif'>{lab}</text>")
    parts.append(f"<line x1='{pad_l}' y1='{pad_t}' x2='{pad_l}' y2='{h - pad_b}' stroke='#333'/>")
    parts.append(f"<line x1='{pad_l}' y1='{h - pad_b}' x2='{w - 10}' y2='{h - pad_b}' stroke='#333'/>")
    parts.append("</svg>")
    _ = path.write_text("\n".join(parts))


def median(xs: list[int]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return float(s[mid]) if n % 2 else (s[mid - 1] + s[mid]) / 2


def main() -> None:
    metric = []
    for name in PROMPTS:
        with (T2 / f"results_{name}.csv").open(newline="") as f:
            rows = list(csv.DictReader(f))
        errs = [abs(int(r["actual_count"]) - int(r["expected_count"])) for r in rows]
        wrong = [e for e, r in zip(errs, rows) if r["correct"] == "0"]
        metric.append({
            "prompt": name,
            "total": len(rows),
            "n_wrong": len(wrong),
            "count_accuracy": sum(1 for e in errs if e == 0) / len(errs),
            "wrong_median": median(wrong),
            "wrong_mean": sum(wrong) / len(wrong) if wrong else 0.0,
            "wrong_max": max(wrong) if wrong else 0,
        })
    _ = (T3 / "metric.json").write_text(json.dumps(metric, indent=2))

    FIGS.mkdir(exist_ok=True)
    labels = [NAMES[m["prompt"]] for m in metric]
    colors = [COLORS[m["prompt"]] for m in metric]
    bar_chart(FIGS / "count_accuracy.svg", "Count accuracy by prompt",
              "share with exact row count", labels,
              [m["count_accuracy"] for m in metric], colors, "{:.2f}")
    bar_chart(FIGS / "wrong_mean.svg", "Mean error over mismatched rows",
              "mean |actual - expected|", labels,
              [m["wrong_mean"] for m in metric], colors, "{:.0f}")

    print("| prompt | count-acc | wrong-median | wrong-mean | n wrong |")
    print("|---|---|---|---|---|")
    for m in metric:
        row_out = (
            f"| {m['prompt']} | {m['count_accuracy']:.2%} | {m['wrong_median']:.0f} "
            f"| {m['wrong_mean']:.1f} | {m['n_wrong']}/{m['total']} |"
        )
        print(row_out)
    print("\nwrote metric.json, figs/count_accuracy.svg, figs/wrong_mean.svg")


if __name__ == "__main__":
    main()
