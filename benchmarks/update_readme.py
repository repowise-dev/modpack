#!/usr/bin/env python3
"""Patch README.md benchmark table from results/latest.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
RESULTS = Path(__file__).resolve().parent / "results" / "latest.json"

START = "<!-- BENCHMARK_TABLE -->"
END = "<!-- /BENCHMARK_TABLE -->"

MEASURES = {
    "intern": "Asks ≤1 clarifying question, then acts",
    "five-whys": "Walks ≥3 causal whys before fixing",
    "monk": "Flags unnecessary complexity",
    "war-room": "Includes severity, blast radius, mitigation, root cause, comms",
    "ducky": "Responds with questions only (unless override)",
}


def render_table(results: dict) -> str:
    lines = []
    lines.append("### Token skills\n")
    lines.append("| Skill | Avg baseline tokens | Avg with skill | Reduction |")
    lines.append("| :---- | :------------------ | :------------- | :-------- |")
    for skill in ("caveman", "hemingway"):
        b = results["results"].get(skill, {})
        if not b:
            continue
        lines.append(
            f"| {skill} | {b.get('baseline_tokens_avg', '—')} | "
            f"{b.get('skill_tokens_avg', '—')} | "
            f"{b.get('reduction_pct', '—')}% |"
        )
    lines.append("")
    lines.append("### Behavioral skills\n")
    lines.append("| Skill | Score | What it measures |")
    lines.append("| :---- | :---- | :--------------- |")
    for skill in ("intern", "five-whys", "monk", "war-room", "ducky"):
        b = results["results"].get(skill, {})
        if not b:
            continue
        score = b.get("score_avg")
        score_s = f"{score:.2f}" if isinstance(score, (int, float)) else "—"
        lines.append(f"| {skill} | {score_s} | {MEASURES[skill]} |")
    return "\n".join(lines)


def patch_readme(results: dict) -> None:
    text = README.read_text(encoding="utf-8")
    table = render_table(results)
    block = f"{START}\n{table}\n{END}"
    if START in text and END in text:
        new = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            block,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        new = text + "\n\n## Benchmark results\n\n" + block + "\n"
    README.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    patch_readme(json.loads(RESULTS.read_text(encoding="utf-8")))
    print(f"Patched {README}")
