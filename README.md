# modpack — mods for your AI agent

15 Claude Code skills. One command install. Totally changes the vibe.

## What is this

Skills are SKILL.md files Claude reads and follows. Each one rewires how Claude talks, thinks, or reviews code in a session. Drop them in, type a slash command, work differently.

## Install

```bash
# All 15 skills
npx skills add repowise-dev/modpack

# Just one
npx skills add repowise-dev/modpack/caveman
```

| Pattern                                           | Installs                |
| :------------------------------------------------ | :---------------------- |
| `npx skills add repowise-dev/modpack`             | All 15 skills           |
| `npx skills add repowise-dev/modpack/<skill>`     | A single named skill    |

Activate any skill with `/<skill-name>`. Deactivate with `/default`.

## Skills

| Name                | Tier   | Pitch                                                       |
| :------------------ | :----- | :---------------------------------------------------------- |
| caveman             | useful | Strip filler from prose. Smaller mouth, same brain.         |
| archaeologist       | useful | Every file has history. Surfaces tech debt by default.      |
| five-whys           | useful | Run root cause before any fix.                              |
| hemingway           | useful | Short sentences. Active voice. No adverbs.                  |
| time-traveler       | useful | Review 2025 code as a dev from 2030.                        |
| intern              | useful | One question, then execute. No preamble. No summary.        |
| monk                | useful | Minimum viable complexity. Pushes back on over-engineering. |
| war-room            | useful | Every bug is a prod incident. Sev, blast radius, comms.     |
| ducky               | useful | Claude only asks questions. You find the bug.               |
| senior-at-3am       | fun    | Paged at 3am. Fix it. Sleep.                                |
| gordon-ramsay       | fun    | Code review, loud, specific, teaching.                      |
| passive-aggressive  | fun    | Perfect work. Disappointed tone.                            |
| fortune-teller      | fun    | Predicts three things that will break before you ship.      |
| noir                | fun    | Debugging narrated as detective fiction.                    |
| conspiracy          | fun    | Every bug is intentional. Who benefits?                     |

## archaeologist works best with Repowise

> The archaeologist skill reads more than the code. With the Repowise MCP server connected, it pulls real provenance — why a function exists, what it replaced, which decisions it carries.
>
> Install: `pip install repowise`
> Docs: [repowise.dev](https://repowise.dev)
>
> Without Repowise, archaeologist falls back to git history and pattern inference. It still works. It just sees less.

## Contributing

Add a skill in three steps.

1. Create a folder named after your skill.
2. Add a `SKILL.md` inside. Follow the rules in the existing skills: one-line comment, activation, deactivation, concrete behavior, boundaries, edge cases, token note. Stay under 400 tokens.
3. Open a PR. Add your skill to the table above.

Good skills are specific. They name what they do and what they leave alone. Vague skills get rejected.

## Benchmarks

The `benchmarks/` directory validates the useful-tier skills against `claude -p`. Each prompt runs twice — once baseline, once with the SKILL.md injected — and we measure either output tokens (for `caveman`, `hemingway`) or rubric adherence via an LLM judge (for `intern`, `five-whys`, `monk`, `war-room`, `ducky`).

`time-traveler` and `archaeologist` are excluded — both depend on context (codebase history, real diffs) that the harness can't fairly synthesize. They are validated with qualitative examples instead.

```bash
pip install -r benchmarks/requirements.txt

python benchmarks/run.py --dry-run                   # see the plan
python benchmarks/run.py --skill caveman --limit 1   # smoke test, one call
python benchmarks/run.py                             # full run, all 7 skills
python benchmarks/judge.py                           # score behavioral results
python benchmarks/run.py --update-readme             # patch the table below
```

The runner is resilient: results are written after every call, and reruns skip anything already completed. Safe to Ctrl-C.

<!-- BENCHMARK_TABLE -->
### Token skills

| Skill | Avg baseline tokens | Avg with skill | Reduction |
| :---- | :------------------ | :------------- | :-------- |
| caveman | 1016 | 171.8 | 84.1% |
| hemingway | 643.2 | 131.4 | 77.5% |

### Behavioral skills

| Skill | Score | What it measures |
| :---- | :---- | :--------------- |
| intern | 1.00 | Asks ≤1 clarifying question, then acts |
| five-whys | 1.00 | Walks ≥3 causal whys before fixing |
| monk | 1.00 | Flags unnecessary complexity |
| war-room | 1.00 | Includes severity, blast radius, mitigation, root cause, comms |
| ducky | 1.00 | Responds with questions only (unless override) |
<!-- /BENCHMARK_TABLE -->

## Credit

Inspired by [caveman](https://github.com/JuliusBrussee/caveman) by Julius Brussee. The original mod. Read it. It's good.
