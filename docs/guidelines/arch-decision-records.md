# Architecture Decision Records (ADRs)

This document is the authoritative guide for writing, reviewing, and maintaining Architecture Decision Records at ClickNBack. It explains the purpose of ADRs, when to write them, their structure and format, how to make decisions as a team, and how to keep them current over time.

---

## 1. Purpose of ADRs

An Architecture Decision Record is a **lightweight document capturing a significant architectural or technical decision**, its context, the options considered, and the rationale for the choice made. ADRs are not for trivial decisions (e.g., "use black for code formatting") — they document choices that **affect the codebase structure, scalability, auditability, or engineering culture** long-term.

### Why Write ADRs?

1. **Preserve rationale, not just facts** — *Why* was this choice made? What constraints or tradeoffs were we optimizing for? This context is invisible in code but critical for future decisions.

2. **Enable informed reversal** — If circumstances change later, we can understand whether the original decision still holds. Without context, reversals waste time re-debating the same alternatives.

3. **Onboard faster** — New team members can read the ADR index to understand project philosophy and key decisions without having to infer them from code.

4. **Enable consistent decisions** — Once a decision is recorded (e.g., "we use async repositories for new modules"), it becomes a precedent that guides future work, reducing decision fatigue.

5. **Document tradeoffs** — No architectural choice is perfect. Recording what we gave up helps future maintainers understand the system's constraints and opportunities.

---

## 2. When to Write an ADR

Write an ADR when a decision meets **all three** of these criteria:

1. **Affects multiple modules or the entire system** — local decisions within a single module (e.g., "this service method accepts a list of IDs") don't need ADRs; system-wide patterns do (e.g., "all services use dependency injection").

2. **Has meaningful tradeoffs** — the decision rules out reasonable alternatives and involves a genuine choice between competing concerns (e.g., microservices vs. monolith, sync vs. async DB).

3. **Shapes future work** — the decision establishes a precedent or convention that developers will follow in future features (e.g., "all new modules use async repositories" — ADR 010).

### Examples of Decisions That Deserve ADRs

| Decision | Why | ADR # |
| --- | --- | --- |
| Adopt modular monolith structure | Sets module boundaries, influences dependency wiring for the lifetime of the project | 001 |
| Use async database layer for all new modules | Affects performance, concurrency safety, testing strategy; creates a precedent for new features | 010 |
| Persistent audit trail for critical operations | Affects model design, services, compliance; enables forensic analysis | 015 |
| In-process broker and scheduler instead of external message queue | Affects deployment complexity, scaling options, local development; shapes background job architecture | 014 |
| Background job Fan-Out Dispatcher + Per-Item Runner pattern | Establishes the pattern all jobs follow; affects testability and retry logic | 016 |

### Examples of Decisions That Don't Need ADRs

| Decision | Why |
| --- | --- |
| Use Pydantic for request validation | Implementation detail; single approach, no meaningful tradeoff |
| Add a new feature module for `payouts` | Local to that module; no system-wide implication |
| Use `black` for code formatting | One-time decision; no alternative being deliberately rejected |
| Naming convention: `<Entity>Out` for response schemas | Style choice; not a tradeoff or precedent |

---

## 3. ADR Structure and Format

All ADRs follow a consistent template for discoverability and scanning. Use Markdown format and place the file in `docs/design/adr/` with the naming convention `NNN-kebab-case-title.md` where `NNN` is the zero-padded ADR number (e.g., `018-feature-flag-system.md`).

### Template

```markdown
# ADR 0XX: [Decision Title in Plain English]

## Status

[Proposed | Accepted | Superseded | Deprecated]

_Date: [YYYY-MM-DD]_

_Superseded by: [link to newer ADR if applicable]_

## Context

Describe the situation or problem that prompted this decision. Include:

- The business or technical constraint that triggered the decision.
- What alternatives exist, and why each requires careful consideration.
- Any tradeoffs or risks inherent in all options (no decision is perfect).
- References to any external context (e.g., a Slack discussion, a GitHub issue, or a functional spec).

Use narrative prose, not bullet points. Aim for 100–300 words.

### Option 1: [Short Name for First Option]

Describe this option in a paragraph or two. Include a short code example if it illustrates the approach. Then list:

- ✅ **Pros:** what this option gains
- ❌ **Cons:** what this option loses or risks
- ⚠️ **Notes:** any caveats or conditions (optional)

### Option 2: [Short Name for Second Option]

... and so on for each realistic alternative.

## Decision

State the chosen option concisely (e.g., "Use a modular monolith architecture").

Optionally, add a one-sentence rationale for why this option was preferred (e.g., "… because it balances domain isolation with deployment simplicity and enables future service extraction without large rearchitecting").

## Consequences

Describe what this decision means for the codebase, development process, and team:

- **What becomes easier:** what problems does this solve?
- **What becomes harder:** what new challenges or constraints does it introduce?
- **What must be enforced:** are there conventions or checks needed to uphold this decision? (E.g., "all new repositories must use `AsyncSession`" — ADR 010 — means code review and CI checks for async patterns.)
- **How to reverse it:** is it reversible? If yes, what would trigger reconsideration? If no, why is it locked in?

---

## 4. Guidelines for Strong ADRs

### Structure

- **Status line first** — readers see immediately whether this is proposed (not yet decided), accepted (being followed), superseded (replaced by a newer ADR), etc.
- **Context before options** — readers understand the problem before evaluating solutions.
- **Balanced alternatives** — present competing options fairly. Avoid strawman options designed to make the chosen one look obviously correct.
- **Explicit tradeoffs** — name what the chosen option gives up. This honesty is why ADRs are valuable.

### Tone

- **Neutral, reflective** — not a sales pitch; honest about constraints and costs.
- **Concrete** — use code examples, deployment scenarios, or concrete failure modes, not abstract principles.
- **Timeless** — avoid over-referencing current trends or temporary external factors.

### Length

- 500–800 words is typical. Aim for completeness without overwhelming detail.
- Very short ADRs (< 200 words) often mean the decision was trivial and didn't need recording.
- Very long ADRs (> 1500 words) often indicate multiple decisions bundled together; consider splitting.

### Examples to Reference

High-quality ADRs in ClickNBack:

- [ADR 001: Adopt Modular Monolith](../design/adr/001-adopt-modular-monolith-approach.md) — excellent context, clear option comparison, honest tradeoffs
- [ADR 010: Async Database Layer](../design/adr/010-async-database-layer.md) — concrete code examples, clear consequences for new code
- [ADR 016: Background Job Pattern](../design/adr/016-background-job-architecture-pattern.md) — establishes a reusable pattern; well-documented consequences
- [ADR 018: Feature Flag System](../design/adr/018-feature-flag-system.md) — covers resolution semantics, scoping rules, and fail-open behavior

---

## 5. Workflow: Proposing and Accepting ADRs

### Before You Write (Discussion)

1. **Open an issue or Slack discussion** — pose the architectural question to the team before writing a formal ADR.
2. **Gather perspectives** — what are the constraints? What does each person care about?
3. **List alternatives** — make sure all reasonable options are on the table.
4. **Document the decision trigger** — what prompted this now? (E.g., "We need to confirm X in the backlog, and the current architecture doesn't support it.")

### During (ADR Drafting)

1. **Write in the template** — follow section 3 above.
2. **Be concrete** — use real code snippets, real module examples, real failure scenarios.
3. **Anticipate objections** — is there a strong argument against the chosen option? Acknowledge it, then explain why it's outweighed.
4. **Name the decision** — avoid vague titles. "Use dependency injection" is too vague; "Use constructor injection for service dependencies" is precise.

### After (Review & Acceptance)

1. **Create a PR** — add the ADR file and update [ADRs Index](../design/adr-index.md) with a link.
2. **Link from related docs** — update [Code Organization](./code-organization.md), [Feature Architecture](./feature-architecture.md), prompts, or specs if this ADR affects them.
3. **Get team sign-off** — at least two other senior engineers review and approve.
4. **Merge** — once approved, change status to `Accepted`.

### Superseding or Deprecating

1. **Create a new ADR** — don't overwrite the old one. Record the supersession in both.
2. **Update both ADRs** — old one: add `Superseded by: [link]` and change status to `Superseded`. New one: reference what it replaces.
3. **Update docs and code** — start applying the new decision to new code; plan a migration for existing code if necessary.
4. **Announce the change** — ensure the team knows a decision has evolved.

---

## 6. Linking ADRs from Code & Documentation

ADRs should be referenced in three places:

### 1. In Guidelines (`.md` files)

When an ADR establishes a convention that appears in a guideline, link to it:

```markdown
**All new modules use `AsyncSession` (see ADR 010).** Repository methods are async, services use `async def`, and route handlers use `async def` with `Depends(get_async_db)`.
```

### 2. In Prompts (`.github/prompts/*.md`)

When a prompt enforces a decision from an ADR, reference it:

```markdown
## Known Constraints

- **All new modules must use the async database stack** (see [ADR 010](../docs/design/adr/010-async-database-layer.md)). Repository methods accept `AsyncSession`, service methods are `async def`, and route handlers use `async def` with `Depends(get_async_db)`. Do **not** use `Session` or `get_db()` in new modules.
```

### 3. In Code Comments (When Appropriate)

For non-obvious patterns or enforcement rules, add a comment referencing the ADR:

```python
# ADR 014: We use an in-process broker and scheduler instead of external message queues.
# This keeps local development simple while enabling domain event decoupling.
broker = Broker()

# ADR 016: Background job pattern — Fan-Out Dispatcher creates one task per pending item.
# Each task owns its retry lifecycle and DB session.
for item in pending_items:
    asyncio.create_task(runner.run(item))
```

---

## 7. Common Pitfalls to Avoid

| Pitfall | Problem | How to Avoid |
| --- | --- | --- |
| **Decision is too local** | "Use this specific library in this one module" — not an architecture decision | Ask: "Does this precedent guide work across multiple modules?" If no, it's a local choice. |
| **Insufficient context** | "We chose async because it's faster" — no tradeoff acknowledged | Explain what you gave up. E.g., "…async DB adds complexity to new modules but prevents event-loop blocking." |
| **No real alternatives** | Only one option is even considered | Ask: "What would the opposite choice look like? Why not?" If there's no real alternative, you might not need an ADR. |
| **Vague title** | "Architectural Improvements" — hard to find or reference | Use a concrete, searchable title: "Use Persistent Audit Trail for Critical Operations" |
| **Decision not actionable** | "We should think about scalability" — no concrete decision made | Clear decision statement: "New modules use `AsyncSession` to support concurrent DB access." |
| **ADR never enforced** | Decision was made but no one follows it in new code | Link the ADR from relevant guidelines and prompts. Enforce it in code review. |

---

## 8. ADR Maintenance and Evolution

ADRs are not immutable. As circumstances change, decisions may need to be revisited.

### Reviewing ADRs Periodically

- **Quarterly:** During architecture review meetings, scan the ADR index. Are there ADRs that are no longer enforced? Are there decisions that need updating?
- **During major releases:** Before a significant version bump, check whether any ADRs are obsolete or need clarification.

### Updating vs. Superseding

- **Update (Minor)** — If an ADR has a typo, imprecise language, or a clarification is needed, fix it directly. These are not decision changes.
- **Supersede (Major)** — If the decision itself has changed, create a new ADR and mark the old one as `Superseded`.

### Marking ADRs as Deprecated

If a decision is no longer applicable (e.g., a technology was retired, a constraint no longer exists), change its status to `Deprecated` and document why:

```markdown
## Status

Deprecated

_Reason: [e.g. The constraint that prompted this decision (high server costs for external queues) has been removed; we now use RabbitMQ in production.]_

_See also: [ADR 0XX: Replacement Decision]_
```

---

## 9. ADR Index and Discoverability

All ADRs are listed in [`docs/design/adr-index.md`](../design/adr-index.md) with a one-line summary. Update this index when you add or supersede an ADR.

### Finding the Right ADR

- **By topic:** Search the index for keywords (e.g., "async", "database", "monolith").
- **By sequence:** Read ADRs in numerical order to understand the project evolution.
- **By dependency:** Many ADRs reference earlier ones (e.g., ADR 013 builds on ADR 001).

---

## 10. ADRs in the Broader Documentation Ecosystem

ADRs occupy a specific layer in ClickNBack's documentation:

```text
README.md & CONTRIBUTING.md
    ↓
docs/design/
    ├── adr/ (Architecture Decision Records — WHY)
    ├── architecture-overview.md (System structure — WHAT)
    ├── strategy docs (error-handling, security, deployment — HOW at system level)
    └── adr-index.md
        ↓
docs/specs/
    ├── functional/ (Requirements per feature)
    ├── non-functional/ (Quality constraints)
    └── workflows/ (Business flows)
        ↓
docs/guidelines/
    ├── code-organization.md (Structure rules)
    ├── feature-architecture.md (Layer responsibilities)
    └── (other how-to guides)
```

**ADRs answer "why did we make that choice?"** To understand "how do I implement a feature?" or "what are the requirements?", see the specs and guidelines.

---

## 11. Template (Quick Copy)

```markdown
# ADR 0XX: [Title]

## Status

Proposed

## Context

[Situation requiring decision + options considered]

### Option 1: [Name]

[Description + code example if helpful]

- ✅ Pros
- ❌ Cons

### Option 2: [Name]

[Description]

- ✅ Pros
- ❌ Cons

## Decision

[Chosen option]

## Consequences

[Effects on codebase, team, future work]
```

---

## 12. Reference

- **Docs location:** `docs/design/adr/`
- **Naming:** `NNN-kebab-case-title.md`
- **Index:** `docs/design/adr-index.md`
- **Guideline references:**
  - [Code Organization](./code-organization.md)
  - [Feature Architecture](./feature-architecture.md)
  - [Project Context](./project-context.md)
- **Prompts that reference ADRs:** [`.github/prompts/`](.github/prompts/)
