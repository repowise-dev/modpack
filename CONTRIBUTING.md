# Contributing to modpack

Thanks for wanting to add a skill. Here's how.

## Adding a new skill

### 1. Create the folder

```
your-skill/
└── SKILL.md
```

Folder name = skill name. Lowercase, hyphens for spaces. This becomes the `/<skill-name>` slash command.

### 2. Write the SKILL.md

Every skill needs YAML frontmatter and a markdown body. Use this template:

```yaml
---
name: your-skill
description: >
  One paragraph. What this skill does, when to use it. Front-load the key
  behavior. Claude uses this description to decide when to auto-load the skill.
---

Direct instructions here. Second person. Imperative. "Do X. Don't do Y."

## Rules

Concrete, numbered rules. Not "be brief" — instead "max 1 sentence per thought, drop articles."

## Boundaries

What this skill does NOT change. Code syntax, error messages, technical accuracy — spell it out.

## Edge cases

What happens when the task is ambiguous, safety-critical, or doesn't fit the skill.
```

### 3. Follow the rules

- **Under 400 tokens.** Skills should be compressed, not verbose. Measure with a tokenizer if unsure.
- **Concrete rules, not vibes.** "Drop articles" is a rule. "Be concise" is a vibe.
- **Define boundaries.** Every skill must say what it does NOT change. Code correctness and technical accuracy should always be preserved.
- **Handle edge cases.** What happens when the user says "just fix it"? When the task is safety-critical? When the skill doesn't apply?
- **Direct imperative prose.** The SKILL.md is injected as instructions. Write it as "Do X" not "When activated, the skill causes Claude to do X."
- **No preamble in the skill itself.** Don't start with "This skill is designed to..." — start with the instructions.

### 4. Test it

Install your skill locally:

```bash
mkdir -p ~/.claude/skills/your-skill
cp your-skill/SKILL.md ~/.claude/skills/your-skill/SKILL.md
```

Open Claude Code, type `/your-skill`, run a few tasks. Verify:
- The behavior is clearly different from baseline
- Code quality isn't degraded
- Edge cases (ambiguous tasks, safety-critical) fall back to normal behavior
- The skill is fun or useful, not just different

### 5. Open the PR

- Add your skill folder with its `SKILL.md`
- Add a row to the skills table in `README.md`
- PR title: `add <skill-name>: one-line description`
- PR body: 2-3 example prompts showing before/after behavior

## Modifying existing skills

Same process. Open a PR. Show before/after of the change. If you're tweaking a benchmarked skill, re-run the relevant benchmark and include the results.

## Running benchmarks

```bash
pip install -r benchmarks/requirements.txt
export GEMINI_API_KEY=your-key

python benchmarks/run.py --skill your-skill   # if applicable
python benchmarks/judge.py --skill your-skill  # if behavioral
```

If adding a new benchmarked skill, also add its prompts to `benchmarks/tasks.json` and rubric to `benchmarks/judge.py`.

## What gets rejected

- Skills that are vague ("be better at code review")
- Skills that degrade code quality or technical accuracy
- Skills that are just prompt wrappers with no specific behavioral rules
- Skills over 400 tokens with no justification
- Skills that duplicate an existing skill's behavior

## Style guide

Look at the existing skills. Match the pattern:
- Frontmatter with `name` and `description`
- Rules section with numbered or bulleted concrete instructions
- Boundaries section
- Edge cases section
- Examples where they help (bad/good pairs)

## Questions?

Open an issue. Keep it short.
