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

### Normal Claude

> "It looks like there's a missing null check on line 34 of auth.ts. The user object could be undefined when the session expires, which would cause the TypeError you're seeing. Let me add a guard clause to fix this."

</td>
<td width="50%">

### 🕵️ `/conspiracy`

> "The missing null check on line 34. Coincidence? The git log says Dave added this line three weeks ago — the same day the error alerts were silently disabled. Two failures of observability in the same sprint. What are the odds. Fixing the null check. But I'm watching Dave."

</td>
</tr>
<tr>
<td>

### Normal Claude

> "Sure! I'd be happy to help you build a config loader. An abstract ConfigSource base class with YamlConfigSource, JsonConfigSource, and EnvConfigSource subclasses sounds like a solid, extensible design..."

</td>
<td>

### 🧘 `/monk`

> "You have 3 file types. That's `json.load()`, `yaml.safe_load()`, and `os.environ` behind an if/elif. One function. No class needed yet."

</td>
</tr>
<tr>
<td>

### Normal Claude

> "The API is returning a 500 error because the database query in getUserProfile() is failing. The user_id parameter is null when the session token expires. Adding a null check before the query should fix it."

</td>
<td>

### 🔍 `/noir`

> "The 500 had been showing up since Tuesday. Nobody noticed. I traced the stack to getUserProfile() — a quiet function in a quiet file. The null was hiding behind an expired session token, waiting for someone to look. I added the check. Case closed. The codebase sleeps tonight."

</td>
</tr>
</table>

**Same fix. Different brain.**

## The Skills

### Useful — change how Claude works

| Skill | What it does | Activate |
|:------|:-------------|:---------|
| **caveman** | Drop articles, filler, preamble. Fragments. Saves ~84% output tokens. Inspired by [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). | `/caveman` |
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
