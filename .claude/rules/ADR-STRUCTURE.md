---
name: adr-structure
type: rule
description: Structure and mandatory sections for Architecture Decision Record documents
---

# ADR-STRUCTURE

## Overview

An Architecture Decision Record (ADR) captures a significant technical decision, its context, alternatives considered, and the rationale. ADRs preserve knowledge and enable informed future decisions.

**Note on Front Matter:** ADRs are regular Markdown files (`.md`) stored in `docs/design/adr/`. Do not add YAML front matter. Per [MARKDOWN-STANDARDS.md](./MARKDOWN-STANDARDS.md), only use official front matter keys (name, type, description) for files in `.claude/` folder. ADR files themselves should not have front matter.

## When to Write an ADR

Write an ADR when **all three** criteria apply:

1. **Affects multiple modules or the entire system** — System-wide patterns, not local decisions.
2. **Has meaningful tradeoffs** — Genuine choice between competing concerns, not an obvious default.
3. **Shapes future work** — Establishes a precedent that guides future features.

**Examples that deserve ADRs:**
- Adopt modular monolith structure
- Use async database layer for all new modules
- In-process broker and scheduler instead of external queue
- Persistent audit trail architecture
- Event-driven audit logging

**Examples that don't need ADRs:**
- Use Pydantic for validation (obvious, single approach)
- Add a new feature module (local decision)
- Use `black` for code formatting (one-time choice)

## Naming Convention

```
docs/design/adr/<NNN-kebab-case-title.md>
```

- **NNN** — Zero-padded sequence (000, 001, ..., 023)

Example: `docs/design/adr/023-event-driven-audit-logging.md`

## Mandatory Sections (In Order)

### 1. Title and Metadata

```markdown
# ADR 0XX: Decision Title in Plain English

## Status

[Proposed | Accepted | Superseded | Deprecated]

_Date: 2024-01-15_

_Superseded by: [link to newer ADR if applicable]_
```

**Status values:**
- **Proposed**: Decision under consideration, not yet accepted.
- **Accepted**: Decision approved and in effect.
- **Superseded**: Replaced by a newer decision (link it).
- **Deprecated**: No longer applicable (explain why).

### 2. Context

```markdown
## Context

Describe the situation that prompted the decision. Include:

- The business or technical problem that needed solving
- What alternatives exist and why each requires careful consideration
- Any tradeoffs or risks inherent in all options
- References to related specs, GitHub issues, or discussions

Example:

ClickNBack began with synchronous database access using SQLAlchemy's session-based ORM. At scale, this model:
- Blocks request threads during database I/O
- Limits concurrency without horizontal scaling
- Complicates testing (blocking operations hard to mock)

We considered three approaches:
1. Async SQLAlchemy 2.0 (modern async support)
2. External task queue (Celery) (shifts complexity, adds ops burden)
3. Thread pool with sync ORM (simpler migration, still blocking)
```

### 3. Options

```markdown
## Options Considered

### Option 1: Async SQLAlchemy 2.0
- Pros: Native async support, no external dependencies, better testing
- Cons: Requires learning new patterns, async/await throughout codebase
- Effort: High (major refactoring)

### Option 2: External Task Queue (Celery)
- Pros: Proven at scale, separates concerns
- Cons: Added deployment complexity, separate process to manage
- Effort: High (new service, new deployment node)

### Option 3: Thread Pool + Sync ORM
- Pros: Smaller migration effort, incremental adoption
- Cons: Still blocking at the thread level, doesn't solve fundamental scalability
- Effort: Medium
```

### 4. Decision

```markdown
## Decision

We adopt **Async SQLAlchemy 2.0** for all new modules.

**Rationale:**
- Eliminates thread blocking and horizontal scaling barriers
- Enables easier testing with AsyncMock patterns
- Aligns with modern Python async ecosystem
- One-time investment pays dividends long-term

**Constraints:**
- Applies to new modules; legacy modules migrate gradually
- All repository methods must be `async def`
- All service write methods accept `UnitOfWorkABC`; read methods accept `AsyncSession`
```

### 5. Consequences

```markdown
## Consequences

### Positive
- Better concurrency: thousands of requests per process without thread overhead
- Cleaner testing: AsyncMock instead of complex thread mocking
- Framework alignment: FastAPI is async-native; this unifies the stack

### Negative
- Learning curve: async/await patterns new to some developers
- Testing complexity: requires pytest-asyncio, careful fixture management
- Debugging: async stack traces can be harder to read

### Implementation Notes
- See ADR-010 for the full async database layer specification
- All repositories must implement `RepositoryABC` with async methods
- Tests must use `AsyncMock()` for DB dependencies
- No blocking I/O (e.g., `requests.get()`) in request handlers
```

## Template

```markdown
# ADR 0XX: [Decision Title]

## Status

[Proposed | Accepted | Superseded | Deprecated]

_Date: YYYY-MM-DD_

## Context

[Describe the problem, alternatives considered, tradeoffs]

## Options Considered

### Option 1: [Name]
- Pros: ...
- Cons: ...
- Effort: ...

### Option 2: [Name]
- Pros: ...
- Cons: ...
- Effort: ...

## Decision

We adopt [decision].

**Rationale:** [Why this option over others]

**Constraints:** [When/where does this apply]

## Consequences

### Positive
- ...

### Negative
- ...

### Implementation Notes
- ...
```

## After Writing an ADR

1. Save to `docs/design/adr/<NNN-kebab-case-title.md` with correct naming
2. Update `docs/design/adr-index.md` — add entry to the index
3. Update any relevant guidelines if the decision affects them
4. If superseding an older ADR, update its status to `Superseded`

---
