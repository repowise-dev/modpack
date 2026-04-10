#!/usr/bin/env python3
"""
modpack benchmark runner — Gemini edition.

Methodology mirrors the JuliusBrussee/caveman reference:
  - direct API call (Gemini generateContent), no agent harness
  - baseline system = "You are a helpful assistant."
  - skill system    = raw SKILL.md content
  - temperature = 0
  - 3 trials per (prompt, mode), output_tokens = median
  - per-prompt savings = 1 - median(skill) / median(baseline)
  - SHA256 of each SKILL.md captured in metadata for reproducibility

Resilient: writes results/latest.json after every single API call.
Reruns skip any (skill, prompt_id, mode, trial) already complete.
Safe to Ctrl-C — at worst you lose the in-flight call.

Auth: requires GEMINI_API_KEY env var.
"""

from __future__ import annotations

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import statistics
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCH = Path(__file__).resolve().parent
TASKS_FILE = BENCH / "tasks.json"
RESULTS_FILE = BENCH / "results" / "latest.json"

DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_TRIALS = 3
TEMPERATURE = 0
MAX_OUTPUT_TOKENS = 4096
CALL_TIMEOUT = 240
RETRY_DELAYS = [5, 10, 20]

BASELINE_SYSTEM = "You are a helpful assistant."

TOKEN_SKILLS = {"caveman", "hemingway"}
BEHAVIORAL_SKILLS = {"intern", "five-whys", "monk", "war-room", "ducky"}
ALL_SKILLS = TOKEN_SKILLS | BEHAVIORAL_SKILLS


# ---------- pretty printing ----------

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        TextColumn,
        TimeElapsedColumn,
    )

    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def say(msg: str, style: str = "") -> None:
    if HAS_RICH:
        console.print(msg, style=style)
    else:
        print(msg, flush=True)


# ---------- io ----------

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_tasks() -> dict[str, list[dict]]:
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def load_skill_md(skill: str) -> str:
    path = ROOT / "skills" / skill / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing SKILL.md for {skill}: {path}")
    return path.read_text(encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_results() -> dict[str, Any]:
    if RESULTS_FILE.exists():
        try:
            return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            say(f"[warn] {RESULTS_FILE} unreadable — starting fresh", "yellow")
    return {
        "started_at": now_iso(),
        "run_at": None,
        "model": DEFAULT_MODEL,
        "trials": DEFAULT_TRIALS,
        "temperature": TEMPERATURE,
        "skill_hashes": {},
        "results": {},
    }


def atomic_write(data: dict[str, Any]) -> None:
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".latest-", suffix=".json", dir=str(RESULTS_FILE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, RESULTS_FILE)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def call_key(prompt_id: str, mode: str, trial: int) -> str:
    return f"{prompt_id}::{mode}::{trial}"


# ---------- gemini api ----------

def gemini_call(
    prompt: str,
    system: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """
    Call Gemini generateContent. Returns the full parsed response dict
    plus a flat 'output_tokens' / 'response_text' for convenience.
    Retries on 429 / 5xx with exponential backoff.
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }
    payload = json.dumps(body).encode("utf-8")

    last_err = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as resp:
                raw = resp.read()
            data = json.loads(raw)

            cands = data.get("candidates") or []
            if not cands:
                raise RuntimeError(f"no candidates in response: {str(data)[:500]}")
            cand = cands[0]
            parts = (cand.get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts)
            usage = data.get("usageMetadata") or {}

            return {
                "ok": True,
                "response_text": text,
                "output_tokens": int(usage.get("candidatesTokenCount", 0) or 0),
                "input_tokens": int(usage.get("promptTokenCount", 0) or 0),
                "thoughts_tokens": int(usage.get("thoughtsTokenCount", 0) or 0),
                "total_tokens": int(usage.get("totalTokenCount", 0) or 0),
                "finish_reason": cand.get("finishReason"),
                "raw": data,
            }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
            last_err = f"HTTP {e.code}: {err_body}"
            if e.code in (429, 500, 502, 503, 504) and attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise RuntimeError(last_err)
        except urllib.error.URLError as e:
            last_err = f"URL error: {e}"
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise RuntimeError(last_err)
    raise RuntimeError(last_err or "unknown gemini error")


# ---------- runner ----------

_INTERRUPTED = False


def _handle_sigint(signum, frame):
    global _INTERRUPTED
    _INTERRUPTED = True
    say("\n[bold yellow]Interrupt — finishing current call, then stopping.[/bold yellow]")


def ensure_skill_bucket(results: dict, skill: str) -> dict:
    bucket = results["results"].setdefault(skill, {})
    bucket.setdefault("type", "token" if skill in TOKEN_SKILLS else "behavioral")
    bucket.setdefault("calls", {})
    return bucket


def run_one(
    prompt_text: str,
    system: str,
    model: str,
    api_key: str,
    prompt_id: str,
    mode: str,
    trial: int,
) -> dict[str, Any]:
    started = now_iso()
    try:
        result = gemini_call(prompt_text, system, model, api_key)
        return {
            **result,
            "mode": mode,
            "prompt_id": prompt_id,
            "trial": trial,
            "started_at": started,
            "finished_at": now_iso(),
        }
    except Exception as e:
        return {
            "ok": False,
            "mode": mode,
            "prompt_id": prompt_id,
            "trial": trial,
            "started_at": started,
            "finished_at": now_iso(),
            "error": str(e)[:1500],
        }


def aggregate(results: dict) -> None:
    """Recompute summary stats per skill. Median across trials, then average."""
    for skill, bucket in results["results"].items():
        calls = bucket.get("calls", {})

        # Group by prompt_id then mode -> list of output_tokens across trials
        per_prompt: dict[str, dict[str, list[int]]] = {}
        per_prompt_text: dict[str, dict[str, list[str]]] = {}
        for key, call in calls.items():
            if not call.get("ok"):
                continue
            try:
                pid, mode, _trial = key.split("::")
            except ValueError:
                continue
            per_prompt.setdefault(pid, {}).setdefault(mode, []).append(call["output_tokens"])
            per_prompt_text.setdefault(pid, {}).setdefault(mode, []).append(call.get("response_text", ""))

        bucket["per_prompt"] = []

        if bucket["type"] == "token":
            base_meds, skill_meds, savings = [], [], []
            for pid in sorted(per_prompt):
                modes = per_prompt[pid]
                b_list = modes.get("baseline", [])
                s_list = modes.get("skill", [])
                if not (b_list and s_list):
                    continue
                bm = statistics.median(b_list)
                sm = statistics.median(s_list)
                save = (1 - sm / bm) if bm > 0 else 0
                base_meds.append(bm)
                skill_meds.append(sm)
                savings.append(save)
                bucket["per_prompt"].append({
                    "prompt_id": pid,
                    "baseline_trials": b_list,
                    "skill_trials": s_list,
                    "baseline_median": int(bm),
                    "skill_median": int(sm),
                    "savings_pct": round(save * 100, 1),
                })
            if base_meds:
                bucket["baseline_tokens_avg"] = round(statistics.mean(base_meds), 1)
                bucket["skill_tokens_avg"] = round(statistics.mean(skill_meds), 1)
                bucket["reduction_pct"] = round(statistics.mean(savings) * 100, 1)
                bucket["min_savings_pct"] = round(min(savings) * 100, 1)
                bucket["max_savings_pct"] = round(max(savings) * 100, 1)
            else:
                bucket["baseline_tokens_avg"] = 0
                bucket["skill_tokens_avg"] = 0
                bucket["reduction_pct"] = 0
        else:
            # behavioral — judge populates scores later. Just record raw.
            for pid in sorted(per_prompt):
                modes = per_prompt[pid]
                bucket["per_prompt"].append({
                    "prompt_id": pid,
                    "baseline_trials_tokens": modes.get("baseline", []),
                    "skill_trials_tokens": modes.get("skill", []),
                })
            bucket.setdefault("score_avg", None)
            bucket.setdefault("score_per_prompt", [])


def main() -> int:
    p = argparse.ArgumentParser(description="modpack benchmark runner (Gemini)")
    p.add_argument("--skill", help="run only this skill")
    p.add_argument("--dry-run", action="store_true", help="print plan, no API calls")
    p.add_argument("--update-readme", action="store_true", help="patch README benchmark table after run")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    p.add_argument("--limit", type=int, default=None, help="first N prompts per skill (smoke test)")
    p.add_argument("--force", action="store_true", help="ignore checkpoint, rerun all")
    p.add_argument("--sleep", type=float, default=0.3, help="seconds to sleep between calls (rate-limit cushion)")
    args = p.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.dry_run:
        say("[red]GEMINI_API_KEY env var not set[/red]")
        return 2

    tasks = load_tasks()
    if args.skill:
        if args.skill not in tasks:
            say(f"[red]unknown skill: {args.skill}. available: {sorted(tasks)}[/red]")
            return 2
        tasks = {args.skill: tasks[args.skill]}
    if args.limit:
        tasks = {k: v[: args.limit] for k, v in tasks.items()}

    plan: list[tuple[str, dict, str, int]] = []
    for skill, prompts in tasks.items():
        for task in prompts:
            for mode in ("baseline", "skill"):
                for trial in range(1, args.trials + 1):
                    plan.append((skill, task, mode, trial))

    say(f"[bold]modpack benchmark[/bold] model={args.model} trials={args.trials} calls={len(plan)}")

    if args.dry_run:
        for skill, task, mode, trial in plan:
            say(f"  {skill:<12} {task['id']:<18} {mode}  t{trial}")
        say(f"[dim]Total API calls: {len(plan)}[/dim]")
        return 0

    if args.force and RESULTS_FILE.exists():
        RESULTS_FILE.unlink()
    results = load_results()
    results["model"] = args.model
    results["trials"] = args.trials
    results["temperature"] = TEMPERATURE

    # preload skill_md + record hashes
    skill_mds = {}
    for skill in tasks:
        md = load_skill_md(skill)
        skill_mds[skill] = md
        results["skill_hashes"][skill] = sha256_text(md)

    signal.signal(signal.SIGINT, _handle_sigint)

    progress = None
    task_id = None
    if HAS_RICH:
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        progress.start()
        task_id = progress.add_task("benchmarking", total=len(plan))

    completed = skipped = failed = 0

    try:
        for skill, task, mode, trial in plan:
            if _INTERRUPTED:
                break
            bucket = ensure_skill_bucket(results, skill)
            key = call_key(task["id"], mode, trial)
            existing = bucket["calls"].get(key)
            if existing and existing.get("ok"):
                skipped += 1
                if progress:
                    progress.update(task_id, advance=1, description=f"skip {skill}/{task['id']}/{mode}/t{trial}")
                continue

            system = skill_mds[skill] if mode == "skill" else BASELINE_SYSTEM
            if progress:
                progress.update(task_id, description=f"{skill}/{task['id']}/{mode}/t{trial}")
            else:
                say(f"  → {skill}/{task['id']}/{mode}/t{trial}")

            call = run_one(
                task["prompt"], system, args.model, api_key,
                task["id"], mode, trial,
            )
            bucket["calls"][key] = call
            if call.get("ok"):
                completed += 1
            else:
                failed += 1
                say(f"    [red]FAIL: {call.get('error','?')[:200]}[/red]")

            results["run_at"] = now_iso()
            aggregate(results)
            atomic_write(results)

            if progress:
                progress.update(task_id, advance=1)

            if args.sleep > 0:
                time.sleep(args.sleep)
    finally:
        if progress:
            progress.stop()

    aggregate(results)
    atomic_write(results)

    say(f"[bold green]done[/bold green] completed={completed} skipped={skipped} failed={failed}")
    say(f"results: {RESULTS_FILE}")

    # quick summary
    for skill, bucket in results["results"].items():
        if bucket["type"] == "token":
            r = bucket.get("reduction_pct")
            if r is not None:
                say(f"  {skill}: avg savings {r}% ({bucket.get('baseline_tokens_avg')} → {bucket.get('skill_tokens_avg')})")

    if args.update_readme:
        try:
            sys.path.insert(0, str(BENCH))
            from update_readme import patch_readme  # type: ignore
            patch_readme(results)
            say("README benchmark table updated")
        except Exception as e:
            say(f"[red]README patch failed: {e}[/red]")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
