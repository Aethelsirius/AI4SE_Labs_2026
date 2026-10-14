import hashlib, json, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

# JSONL parsing below is inherently untyped (json.loads -> Any).
# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false

T2 = Path(__file__).resolve().parent
T1 = T2.parent / "Task_1"
ROOT = T2.parents[2]
PROMPTS = ["rtf", "fewshot", "cot"]


def parse_jsonl(stdout: str) -> dict[str, str | None]:
    model: str | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        rtype = rec.get("type")
        data = rec.get("data", {}) if isinstance(rec.get("data"), dict) else {}
        if rtype == "session.auto_mode_resolved" and model is None:
            model = data.get("chosenModel") or model
        elif rtype == "assistant.message":
            model = data.get("model") or model
        elif rtype == "model.call_start" and model is None:
            model = data.get("model") or model
    return {
        "model_resolved": model,
    }


def main():
    (T2 / "logs").mkdir(exist_ok=True)
    for name in PROMPTS:
        prompt = (T1 / f"{name}.md").read_text()
        out_csv = T2 / f"predictions_{name}.csv"
        if out_csv.exists():
            out_csv.unlink()
        cmd = ["copilot", "-p", prompt, "--no-ask-user", "--output-format", "json"]
        start = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        try:
            r = subprocess.run(
                cmd,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=900,
            )
            rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
        except subprocess.TimeoutExpired as e:
            rc = 124
            out_s: str = (
                e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            )
            err_s: str = (
                e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            )
            out, err = out_s, err_s + "\nTIMEOUT after 900s"
        wall = time.perf_counter() - t0
        info = parse_jsonl(out)
        meta = {
            "prompt": name,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "started_utc": start,
            "ended_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": wall,
            "returncode": rc,
            "model_resolved": info["model_resolved"],
            "stdout_tail": out[-2000:],
            "stderr_tail": err[-2000:],
        }
        _ = (T2 / "logs" / f"{name}.json").write_text(json.dumps(meta, indent=2))
        print(f"{name}: rc={rc} {wall:.1f}s -> {out_csv.name}")
        if rc != 0 or not out_csv.exists():
            print(f"STOP: {name} failed, see logs/{name}.json")
            break


if __name__ == "__main__":
    main()
