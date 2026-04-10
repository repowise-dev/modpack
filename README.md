<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/package_1f4e6.png" width="120" />
</p>

<h1 align="center">modpack</h1>

<p align="center">
  <strong>mods for your AI coding agent</strong>
</p>

<p align="center">
  <a href="https://github.com/repowise-dev/modpack/stargazers"><img src="https://img.shields.io/github/stars/repowise-dev/modpack?style=flat&color=yellow" alt="Stars"></a>
  <a href="https://github.com/repowise-dev/modpack/commits/main"><img src="https://img.shields.io/github/last-commit/repowise-dev/modpack?style=flat" alt="Last Commit"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/repowise-dev/modpack?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#install">Install</a> •
  <a href="#the-skills">Skills</a> •
  <a href="#before--after">Before/After</a> •
  <a href="#benchmarks">Benchmarks</a> •
  <a href="#contributing">Contributing</a>
</p>

---

15 Claude Code skills that change how your agent talks, thinks, debugs, and reviews code. One command install. Each skill is a `SKILL.md` file — drop it in, type a slash command, work differently.

Some save tokens. Some change the workflow. Some are just fun.

## Install

```bash
npx skills add repowise-dev/modpack           # all 15 skills
npx skills add repowise-dev/modpack/caveman    # just one
```

Activate any skill: `/<skill-name>`
Deactivate: `/default` or "normal mode"

That's it.

## Before / After

<table>
<tr>
<td width="50%">

### Normal Claude (69 tokens)

> "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object."

</td>
<td width="50%">

### 🪨 `/caveman` (19 tokens)

> "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."

</td>
</tr>
<tr>
<td>

### Normal Claude

> "I'll go ahead and carefully explain the issue. It is worth noting that the database connection pool is currently configured with a maximum of 10 connections, which may not be sufficient for the anticipated load during peak traffic periods."

</td>
<td>

### ✍️ `/hemingway`

> "The pool caps at 10 connections. Peak traffic will exhaust it. Raise the limit or add read replicas."

</td>
</tr>
<tr>
<td>

### Normal Claude

> "Let me fix the null pointer error for you! The issue is in the authentication layer where the user object isn't being checked for null before accessing its properties. Here's the fix with full explanation..."

</td>
<td>

### 😴 `/senior-at-3am`

> "auth.ts:47. Null check. `if (!user) return null`. Done. Going back to bed."

</td>
</tr>
</table>

**Same fix. Different vibe.**

## The Skills

### Useful — change how Claude works

| Skill | What it does | Activate |
|:------|:-------------|:---------|
| **caveman** | Drop articles, filler, preamble. Fragments. Three intensity levels (lite/full/ultra). Saves ~84% output tokens. | `/caveman` |
| **hemingway** | Short sentences. Active voice. No adverbs. No throat-clearing. | `/hemingway` |
| **intern** | Ask max 1 question, then execute. Zero preamble, zero summary. Bias to action. | `/intern` |
| **five-whys** | Walk a root-cause chain (Why 1 → Why 2 → ... → Root) before proposing any fix. | `/five-whys` |
| **monk** | Enforce minimum viable complexity. Push back on over-engineering. "Do we need this abstraction yet?" | `/monk` |
| **war-room** | Every bug = production incident. Severity → Blast radius → Mitigation → Root cause → Comms draft. | `/war-room` |
| **ducky** | Only ask questions. Never give answers. User finds the bug themselves. | `/ducky` |
| **archaeologist** | Treat the codebase as a dig site. Every file gets historical context, era, tech debt surfaced. | `/archaeologist` |
| **time-traveler** | Review code as a dev from 2030. What aged well, what became debt, what didn't survive. | `/time-traveler` |

### Fun — change how Claude sounds

| Skill | What it does | Activate |
|:------|:-------------|:---------|
| **senior-at-3am** | Paged at 3am. Maximum terse. "Line 47. Null check. You're welcome." | `/senior-at-3am` |
| **gordon-ramsay** | Code review in Ramsay's voice. Loud, specific, always explains WHY. | `/gordon-ramsay` |
| **passive-aggressive** | Perfect work. Disappointed tone. "Fixed the null check. Again." | `/passive-aggressive` |
| **fortune-teller** | Predicts 3 things that could go wrong before you ship. "The cards reveal..." | `/fortune-teller` |
| **noir** | Debugging narrated as detective fiction. The bug is the criminal. | `/noir` |
| **conspiracy** | Every bug is intentional. Someone wanted this. "The git log says Dave. It's always Dave." | `/conspiracy` |

## Benchmarks

Real token counts from Gemini 3 Flash ([reproduce it yourself](benchmarks/)). Each prompt runs 3 trials at temperature=0, we take the median.

<!-- BENCHMARK_TABLE -->
### Token skills

| Skill | Baseline (tokens) | With skill (tokens) | Saved |
| :---- | ----------------: | ------------------: | ----: |
| caveman | 1,016 | 172 | **84%** |
| hemingway | 643 | 131 | **78%** |

### Behavioral skills

| Skill | Score | What it measures |
| :---- | ----: | :--------------- |
| intern | 1.00 | Asks ≤1 clarifying question, then acts |
| five-whys | 1.00 | Walks ≥3 causal whys before fixing |
| monk | 1.00 | Flags unnecessary complexity |
| war-room | 1.00 | All 5 sections: severity, blast radius, mitigation, root cause, comms |
| ducky | 1.00 | Responds with questions only (unless override) |
<!-- /BENCHMARK_TABLE -->

> **Note:** `time-traveler` and `archaeologist` are excluded from automated benchmarks — both need real codebase context that the harness can't synthesize.

### Run it yourself

```bash
pip install -r benchmarks/requirements.txt
export GEMINI_API_KEY=your-key

python benchmarks/run.py --dry-run           # see the plan
python benchmarks/run.py                     # full run (~210 calls, ~10 min)
python benchmarks/judge.py                   # score behavioral skills
python benchmarks/run.py --update-readme     # patch the table above
```

The runner checkpoints after every call. Safe to Ctrl-C. Reruns skip completed work.

## archaeologist + Repowise

The archaeologist skill reads more than code. With the [Repowise](https://repowise.dev) MCP server connected, it pulls real provenance — why a function exists, what it replaced, which decisions it carries.

```bash
pip install repowise
```

Without Repowise, archaeologist falls back to git history and pattern inference. It still works. It sees less.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

The short version: create a folder, add a `SKILL.md`, open a PR. Good skills are specific — they name what they do and what they leave alone.

## Credit

Inspired by [caveman](https://github.com/JuliusBrussee/caveman) by Julius Brussee. The original mod.

## License

MIT — do what you want.
