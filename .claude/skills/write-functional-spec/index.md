---
name: write-functional-spec
type: skill
description: Write a functional specification document
---

# Skill: Write Functional Spec

Write a functional specification document — the single source of truth for a feature.

## Before Starting

1. **Clarify scope** — Is this one feature (one user action) or multiple?
2. **Check indexing** — Reserve the next XX-NN sequence number from `docs/specs/functional/<domain>/`
3. **Read FUNCTIONAL-SPEC-STRUCTURE rule** — Covers all mandatory sections

## Workflow

### Section 1: Title & Preamble

```markdown
# PU-01: Purchase Ingestion

IMPORTANT: This is a living document. Specifications are subject to change.
```

### Section 2: User Story

```markdown
## User Story

_As a registered user, I want to submit a purchase so that I can earn cashback._
```

### Section 3: Domain Concepts (If Needed)

Define unfamiliar domain terms.

### Section 4: Constraints

List exhaustively:
- **Authorization**: Who can perform this action?
- **Input validation**: What fields are required, what ranges are acceptable?
- **Data dependencies**: What must exist (merchant, offer, user)?
- **Idempotency**: Is this idempotent? What makes it unique?

### Section 5: BDD Acceptance Criteria

List scenarios covering:
- Happy path
- Auth failures (if applicable)
- Validation failures
- Business rule failures

Each scenario: Given → When → Then format.

### Section 6: Use Cases

Describe workflows:
- Main happy-path flow (step-by-step)
- Alternate flows (failures, edge cases)

### Section 7: API Contract Link

```markdown
## API Contract

[create-purchase (API contract)](../../docs/design/api-contracts/purchases/create-purchase.md)
```

---
