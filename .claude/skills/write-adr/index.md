---
name: write-adr
type: skill
description: Write an Architecture Decision Record
---

# Skill: Write ADR

Write an Architecture Decision Record — document a significant technical decision and its rationale.

## Should You Write an ADR?

Write an ADR only if **all three** apply:

1. ✅ Affects multiple modules or the entire system
2. ✅ Has meaningful tradeoffs (alternatives with pros/cons)
3. ✅ Shapes future work (establishes precedent)

If only 1–2 apply, document in a comment or in the code instead.

## Before Starting

1. **Check `docs/design/adr-index.md`** — What number should this be?
2. **Gather context** — Options, tradeoffs, constraints
3. **Read ADR-STRUCTURE rule** — Covers all mandatory sections

## Workflow

### Section 1: Title & Status

```markdown
# ADR 0XX: Decision Title in Plain English

## Status

[Proposed | Accepted | Superseded | Deprecated]

_Date: 2024-01-15_
```

### Section 2: Context

Describe the problem:
- Business/technical constraint that triggered the decision
- What alternatives were considered
- Tradeoffs inherent in all options

### Section 3: Options Considered

For each option, include Pros, Cons, and Effort.

### Section 4: Decision

State which option was chosen and why.

### Section 5: Consequences

Positive consequences, negative consequences, implementation notes.

---
