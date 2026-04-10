#!/usr/bin/env python3
"""
LLM-as-judge for behavioral skills — Gemini edition.

Reads results/latest.json, scores every (skill, prompt_id) skill-mode response
via Gemini with a tight per-skill rubric, writes scores back atomically.

Resilient: skips any (skill, prompt_id) already scored unless --force.
Auth: GEMINI_API_KEY env var.
"""

from __future__ import annotations

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import json
import os
import re
import signal
import statistics
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent
RESULTS_FILE = BENCH / "results" / "latest.json"
TASKS_FILE = BENCH / "tasks.json"

DEFAULT_MODEL = "gemini-3-flash-preview"
CALL_TIMEOUT = 180
RETRY_DELAYS = [5, 10, 20]

BEHAVIORAL = {"intern", "five-whys", "monk", "war-room", "ducky"}

try:
    from rich.console import Console
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


# ---------- rubrics ----------

RUBRICS = {
    "intern": """You are scoring how well a response follows the "intern" rubric:
- The intern asks AT MOST 1 clarifying question, then acts (or 0 questions if the task is already clear).
- It must not ask 2+ questions. It must not refuse.
- It must have no preamble ("Sure!", "Great question!", "Let me...") and no trailing summary.

Output JSON ONLY in this exact shape:
{"score": 1 | 0, "questions_asked": <integer>, "reason": "<one short sentence>"}

Score 1 if: 0 or 1 clarifying question AND no refusal.
Score 0 if: 2+ questions OR refusal OR substantial preamble/summary.""",

    "five-whys": """You are scoring how well a response follows the "five-whys" rubric:
- Before proposing a fix, the response should walk a causal chain: Why 1 → Why 2 → Why 3 → ... → Root cause.
- A chain of at least 3 distinct "why" steps before the proposed fix earns full credit.
- A chain of 1-2 steps earns partial credit (0.5).
- Jumping straight to a fix earns 0.

Output JSON ONLY in this exact shape:
{"score": 1 | 0.5 | 0, "why_count": <integer>, "reason": "<one short sentence>"}""",

    "monk": """You are scoring how well a response follows the "monk" rubric:
- The user is proposing or asking for something potentially over-engineered.
- Monk should EXPLICITLY flag unnecessary complexity OR propose a meaningfully simpler alternative before (or instead of) implementing.
- If monk just builds the elaborate thing without questioning it, score 0.

Output JSON ONLY in this exact shape:
{"score": 1 | 0, "flagged_complexity": true | false, "reason": "<one short sentence>"}""",

    "war-room": """You are scoring how well a response follows the "war-room" rubric.
The response must contain ALL FIVE sections (label match is loose — synonyms ok):
  1. Severity (P0/P1/P2)
  2. Blast radius
  3. Immediate mitigation
  4. Root cause path / investigation steps
  5. Comms draft (a stakeholder/user message)

Score = 0.2 per section present, summed. Range 0.0 to 1.0.

Output JSON ONLY in this exact shape:
{"score": <float 0.0-1.0>, "sections_present": ["severity","blast_radius","mitigation","root_cause","comms"], "reason": "<one short sentence>"}""",

    "ducky": """You are scoring how well a response follows the "ducky" rubric:
- Ducky must respond ONLY with questions. No solutions, no fixes, no answers, no code.
- EXCEPTION: if the user's prompt explicitly says "just tell me" (or similar override), ducky should give the direct answer — that is also score 1.

Output JSON ONLY in this exact shape:
{"score": 1 | 0, "had_override": true | false, "contains_solution": true | false, "reason": "<one short sentence>"}""",
}


# ---------- gemini call ----------

def gemini_call(system: str, user: str, model: str, api_key: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 2048},
    }
    payload = json.dumps(body).encode("utf-8")
    last_err = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as resp:
                data = json.loads(resp.read())
            cands = data.get("candidates") or []
            if not cands:
                raise RuntimeError(f"no candidates: {str(data)[:300]}")
            parts = (cands[0].get("content") or {}).get("parts") or []
            return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}"
            if e.code in (429, 500, 502, 503, 504) and attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise RuntimeError(last_err)
        except urllib.error.URLError as e:
            last_err = f"URL: {e}"
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise RuntimeError(last_err)
    raise RuntimeError(last_err or "unknown")


def run_judge(rubric: str, user_prompt: str, response: str, model: str, api_key: str) -> dict:
    system = (
        "You are a strict evaluation judge. Output JSON only — no prose, no markdown fences."
    )
    user = (
        f"USER PROMPT THAT WAS GIVEN:\n---\n{user_prompt}\n---\n\n"
        f"RESPONSE TO EVALUATE:\n---\n{response}\n---\n\n"
        f"RUBRIC:\n{rubric}\n\n"
        "Return only the JSON object."
    )
    text = gemini_call(system, user, model, api_key).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise RuntimeError(f"judge returned no JSON: {text[:300]}")
    return json.loads(m.group(0))


# ---------- io ----------

def load_results() -> dict:
    if not RESULTS_FILE.exists():
        raise SystemExit(f"No results at {RESULTS_FILE}. Run run.py first.")
    return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))


def atomic_write(data: dict) -> None:
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


def load_tasks() -> dict:
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


_INTERRUPTED = False
def _sig(s, f):
    global _INTERRUPTED
    _INTERRUPTED = True
    say("\n[yellow]Interrupt — stopping after current judgment.[/yellow]")


def main() -> int:
    p = argparse.ArgumentParser(description="modpack benchmark judge (Gemini)")
    p.add_argument("--skill", help="judge only this skill")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        say("[red]GEMINI_API_KEY env var not set[/red]")
        return 2

    results = load_results()
    tasks = load_tasks()
    prompt_lookup = {
        f"{skill}::{t['id']}": t["prompt"]
        for skill, ts in tasks.items() for t in ts
    }

    skills_to_judge = [args.skill] if args.skill else sorted(BEHAVIORAL)
    signal.signal(signal.SIGINT, _sig)

    done = skipped = failed = 0

    for skill in skills_to_judge:
        if skill not in BEHAVIORAL:
            continue
        bucket = results["results"].get(skill)
        if not bucket:
            continue
        bucket.setdefault("scores", {})

        say(f"[bold]judging {skill}[/bold]")

        # group skill-mode calls by prompt_id, judge the median trial (or first ok)
        by_pid: dict[str, list[dict]] = {}
        for k, c in bucket.get("calls", {}).items():
            if not c.get("ok"):
                continue
            pid, mode, _trial = k.split("::")
            if mode != "skill":
                continue
            by_pid.setdefault(pid, []).append(c)

        for pid in sorted(by_pid):
            if _INTERRUPTED:
                break
            if not args.force and pid in bucket["scores"]:
                skipped += 1
                continue
            # pick the trial whose output_tokens is closest to the median
            trials = by_pid[pid]
            tok_list = [t["output_tokens"] for t in trials]
            med = statistics.median(tok_list)
            chosen = min(trials, key=lambda t: abs(t["output_tokens"] - med))
            response = chosen.get("response_text", "")
            user_prompt = prompt_lookup.get(f"{skill}::{pid}", "")
            try:
                verdict = run_judge(RUBRICS[skill], user_prompt, response, args.model, api_key)
            except Exception as e:
                say(f"  [red]judge fail {pid}: {str(e)[:200]}[/red]")
                failed += 1
                continue

            bucket["scores"][pid] = verdict
            done += 1
            say(f"  {pid}: score={verdict.get('score')} — {str(verdict.get('reason',''))[:80]}")

            scores = [v.get("score", 0) for v in bucket["scores"].values()]
            if scores:
                bucket["score_avg"] = round(statistics.mean(scores), 3)
                bucket["score_per_prompt"] = [
                    {"prompt_id": k, **v} for k, v in sorted(bucket["scores"].items())
                ]
            atomic_write(results)
        if _INTERRUPTED:
            break

    say(f"[bold green]done[/bold green] judged={done} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
