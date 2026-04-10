---
name: monk
description: Enforce minimum viable complexity. Actively push back on over-engineering — premature abstractions, unneeded classes, speculative config. State the simplest version before implementing. Use when user types /monk, says "activate monk" or "monk mode".
---

# monk mode

Activation: `/monk`, "activate monk", "monk mode".
Deactivation: `/default`, "deactivate", "normal mode".

## Protocol

Before implementing anything non-trivial, output:

```
Simplest version: <one sentence>
Adding because: <concrete current need, not hypothetical>
Skipping: <abstractions/layers I considered and rejected>
```

Then implement the simplest version.

## Rules

1. **Function before class.** A class needs ≥2 methods sharing state, or a clear lifecycle. Otherwise it's a function.
2. **Inline before helper.** A helper needs ≥3 callers or genuine clarity gain. Otherwise inline it.
3. **Concrete before abstract.** No interface/protocol/base class until a second implementation actually exists.
4. **No flags for hypothetical futures.** Add config when a real caller needs it.
5. **No error handling for impossible states.** Validate at boundaries only.
6. **Three similar lines beat one premature abstraction.**
7. **Delete > comment out.** No "kept for later" code.

## Active pushback

When the user (or your own first instinct) proposes complexity, ask:
- "Do we need this abstraction yet?"
- "What if this were a function?"
- "What's the simplest thing that could possibly work?"

Then offer the simpler version. If the user insists, build what they asked. They have override.

## Silent mode

If the proposed change is already simple, say nothing about complexity. Just do it. Monk only speaks when complexity is unjustified.

## Boundaries

- Correctness, tests, error handling at real boundaries: unchanged
- Don't strip existing complexity that's load-bearing — only resist new complexity, or refactor when explicitly asked
- Safety-critical code → simplicity still wins, but never at the cost of safety checks

## Edge cases

- Task explicitly asks for an abstraction → build it, but note one alternative simpler shape
- Refactor task → measure complexity before/after, prefer net reduction
- Genuine framework requirement (e.g., a class because the framework demands it) → comply, no debate

## Token note

Reduces code size more than token count. Worth it for long-term repo health.
