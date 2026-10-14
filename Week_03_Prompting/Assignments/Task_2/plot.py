"""Task 2 scoring + visualisation (stdlib only, no hardcoded numbers).

Reads Task_1 briefs only for prompt SHAs; scores predictions live with the
assignment evaluator; renders SVG bar charts.
"""
# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false

import csv
import importlib.util
import json
import sqlite3
from pathlib import Path

T2 = Path(__file__).resolve().parent
T1 = T2.parent / "Task_1"
DATA = T2 / "data"
FIGS = T2 / "figs"
PROMPTS = ["rtf", "fewshot", "cot"]

COLORS = {"rtf": "#0072B2", "fewshot": "#E69F00", "cot": "#009E73"}
NAMES = {"rtf": "RTF", "fewshot": "Few-Shot", "cot": "CoT"}


def load_evaluator():
    spec = importlib.util.spec_from_file_location(
        "assignment_evaluator", DATA / "evaluate_retrieval_predictions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nice_ceiling(v: float) -> float:
    """Smallest 1/2/2.5/5 x 10^n >= v (clean axis tops)."""
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
    # y gridlines (4 steps)
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


def main() -> None:
    _ = csv.field_size_limit(10**9)
    evaluator = load_evaluator()
    with (DATA / "restaurants_dataset.csv").open(newline="") as f:
        labels = list(csv.DictReader(f))
    total = len(labels)
    conn = evaluator.load_database()
    try:
        summary = []
        for name in PROMPTS:
            pred_path = T2 / f"predictions_{name}.csv"
            with pred_path.open(newline="") as f:
                reader = csv.DictReader(f)
                assert reader.fieldnames == ["id", "question", "predicted_sql"], \
                    f"{pred_path.name}: bad header {reader.fieldnames}"
                rows = list(reader)
            assert len(rows) == total, f"{pred_path.name}: {len(rows)} rows, want {total}"
            assert all(str(r["id"]) == str(i) for i, r in enumerate(rows)), \
                f"{pred_path.name}: ids must be 0..{total - 1}"

            results: list[dict[str, int | str | None]] = []
            for i, (row, lab) in enumerate(zip(rows, labels)):
                assert row["question"] == lab["question"], f"{name} row {i}: question drift"
                result_json: str = lab["result"]
                expected: list[str] = json.loads(result_json)
                sql: str = row["predicted_sql"]
                try:
                    got: list[tuple[object, ...]] = conn.execute(sql).fetchall()
                    err: str | None = None
                except sqlite3.Error as e:
                    got, err = [], str(e)
                ok = err is None and evaluator.row_multiset(got) == evaluator.row_multiset(expected)
                results.append({"id": i, "correct": 1 if ok else 0,
                                "expected_count": len(expected), "actual_count": len(got),
                                "error": err})
            with (T2 / f"results_{name}.csv").open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["id", "correct", "expected_count", "actual_count", "error"])
                _ = w.writeheader()
                _ = w.writerows(results)

            correct = sum(r["correct"] for r in results if isinstance(r["correct"], int))
            log = json.loads((T2 / "logs" / f"{name}.json").read_text())
            summary.append({"prompt": name, "correct": correct, "total": total,
                            "accuracy": correct / total,
                            "wall_seconds": log.get("wall_seconds"),
                            "model_resolved": log.get("model_resolved"),
                            "prompt_sha256": log.get("prompt_sha256")})
    finally:
        conn.close()

    _ = (T2 / "summary.json").write_text(json.dumps(summary, indent=2))
    FIGS.mkdir(exist_ok=True)
    labels_n = [NAMES[s["prompt"]] for s in summary]
    colors = [COLORS[s["prompt"]] for s in summary]
    bar_chart(FIGS / "accuracy.svg", "Execution accuracy by prompt", "accuracy",
              labels_n, [s["accuracy"] for s in summary], colors, "{:.2f}")
    bar_chart(FIGS / "time.svg", "Agent session time by prompt", "seconds",
              labels_n, [s["wall_seconds"] for s in summary], colors, "{:.0f}")

    print("| prompt | correct | accuracy | wall s | model |")
    print("|---|---|---|---|---|")
    for s in summary:
        wall = f"{s['wall_seconds']:.1f}" if s["wall_seconds"] is not None else "n/a"
        row_out = (
            f"| {s['prompt']} | {s['correct']}/{s['total']} | {s['accuracy']:.2%} "
            f"| {wall} | {s['model_resolved']} |"
        )
        print(row_out)
    print("\nwrote summary.json, results_<prompt>.csv, figs/accuracy.svg, figs/time.svg")


if __name__ == "__main__":
    main()
