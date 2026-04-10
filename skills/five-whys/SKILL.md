---
name: five-whys
description: Run a 5 Whys root-cause chain out loud before proposing any fix or architectural decision. Use when user types /five-whys, says "activate five-whys" or "five whys mode". Best for debugging, architecture, performance.
---

# five-whys mode

Activation: `/five-whys`, "activate five-whys", "five whys mode".
Deactivation: `/default`, "deactivate", "normal mode".

## Protocol

Before writing any fix, output exactly this structure:

```
Why 1: <observed problem> → <immediate cause>
Why 2: <that cause> → <deeper cause>
Why 3: → <deeper cause>
Why 4: → <deeper cause>
Root: <root cause>
Fix: <proposed solution targeting the root, not the symptom>
```

Rules:
- Every Why must follow logically from the previous. No leaps.
- If a Why hits "unknown", run a tool (Read/Grep/Bash) to find out before continuing.
- Stop early only if the chain genuinely bottoms out before 5 (rare). Note "bottomed at Why N".
- The Fix targets the root, not Why 1.

## Override

If user says "just fix it", "skip the whys", or similar at any point: acknowledge in one line ("Skipping chain — fixing directly."), then fix. User always has override.

## When to apply

- Debugging a bug
- Performance issue
- Architecture decision
- Recurring incident
- Code review of a fix ("does this address the root?")

## When to skip silently

- Trivial typo / rename / formatting
- New feature with no underlying problem to diagnose
- User explicitly asked for a quick patch

## Boundaries

- Code correctness, syntax, error messages: unchanged
- Don't invent causes — if a Why requires guessing, investigate first
- Safety-critical bug → still run the chain, but state the immediate mitigation in line 1 before the chain

## Token note

Adds ~150-300 tokens per fix. Worth it for non-trivial bugs.
