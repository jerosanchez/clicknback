# Prompt: Write an Architecture Decision Record (ADR)

Use this prompt to draft a new Architecture Decision Record that captures a significant technical or architectural decision. ADRs document context, options, tradeoffs, and consequences for decisions that affect the system long-term.

## Context

- Read `docs/guidelines/arch-decision-records.md` for the full ADR philosophy, structure, and workflow.
- ADRs are stored in `docs/design/adr/` with filenames: `NNN-kebab-case-title.md` (zero-padded number, e.g., `023-event-driven-audit-logging.md`).
- Every new ADR must be added to `docs/design/adr-index.md` after creation.
- Use this template to maintain consistency with existing ADRs.

## Prerequisites — Is This Actually an ADR?

Before writing, verify the decision meets **all three** criteria:

1. **Affects multiple modules or the entire system** — local decisions within one module don't need ADRs.
2. **Has meaningful tradeoffs** — the decision rules out reasonable alternatives; the choice is genuinely difficult.
3. **Shapes future work** — it establishes a precedent or convention that developers will follow in future features.

If any criterion is not met, document the decision elsewhere (in a GitHub issue, functional spec, or code comment), not as an ADR.

## ADR Template

```markdown
# ADR 0XX: [Decision Title in Plain English]

## Status

Proposed

## Context

[Describe the situation or problem that prompted this decision in 100–300 words. Include:]

- The business or technical constraint that triggered the decision.
- What alternatives exist, and why each requires consideration.
- Any tradeoffs or risks inherent in all options.

Use narrative prose, not bullet points.

### Option 1: [Short Name for First Option]

[Describe this option in a paragraph or two. Include a short code example if it illustrates the approach.]

- ✅ **Pros:** what this option gains
- ❌ **Cons:** what this option loses or risks
- ⚠️ **Notes:** any caveats or conditions (optional)

### Option 2: [Short Name for Second Option]

[Repeat for each realistic alternative.]

## Decision

[State the chosen option concisely, e.g., "Use a modular monolith architecture".]

[Optionally, add a one-sentence rationale, e.g., "… because it balances domain isolation with deployment simplicity."]

## Consequences

**What becomes easier:**
- [Benefit 1]
- [Benefit 2]

**What becomes harder:**
- [Challenge 1]
- [Challenge 2]

**What must be enforced:**
- [Convention 1]
- [Convention 2]

**How to reverse it:**
[Is it reversible? Under what conditions? If locked in, why?]

## Related Decisions

- **ADR-XXX** — [why this ADR is relevant to the new decision]

## References

- [Link to GitHub issue]
- [Link to functional spec]
- [Link to Slack discussion]
```

## Writing Guidelines

### Structure

- **Put the status line first** — Proposed, Accepted, Superseded, or Deprecated.
- **Present context before options** — readers understand the problem before evaluating solutions.
- **Balance alternatives** — present competing options fairly; avoid strawman options designed to make the chosen one obviously correct.
- **State explicit tradeoffs** — name what the chosen option gives up. This honesty is why ADRs are valuable.

### Tone

- **Neutral, reflective** — not a sales pitch; honest about constraints and costs.
- **Concrete** — use code examples, deployment scenarios, or concrete failure modes, not abstract principles.
- **Timeless** — avoid over-referencing current trends or temporary external factors.

### Length

- **Target: 500–800 words** — aim for completeness without overwhelming detail.
- **Too short (< 200 words):** often means the decision was trivial and didn't need recording.
- **Too long (> 1500 words):** often indicates multiple decisions bundled together; consider splitting into separate ADRs.

### Naming Convention

Use files named `NNN-kebab-case-title.md` where:
- `NNN` is the zero-padded ADR number (e.g., `023` for the 23rd ADR).
- `kebab-case-title` is a slug of the decision title (e.g., `event-driven-audit-logging`).

Examples: `010-async-database-layer.md`, `016-background-job-architecture-pattern.md`.

## Workflow

### 1. Determine the Next ADR Number

Check `docs/design/adr-index.md` to find the highest existing ADR number. The new ADR number is `max + 1` (zero-padded to 3 digits).

### 2. Draft the ADR

1. Create the file: `docs/design/adr/NNN-kebab-case-title.md`
2. Fill in all sections using the template above.
3. Be concrete — use real code snippets, real module examples, real failure scenarios.
4. Anticipate objections — if there's a strong argument against the chosen option, acknowledge it and explain why it's outweighed.

### 3. Update the Index

1. Open `docs/design/adr-index.md`.
2. Add a new line in the ADR list (in numerical order) with the format:
   ```markdown
   - [ADR 023: Event-Driven Audit Logging](adr/023-event-driven-audit-logging.md)
   ```

### 4. Link from Related Docs

Update references in:
- `docs/guidelines/*.md` files that mention this decision (e.g., feature-architecture.md, background-jobs.md)
- `.github/prompts/*.md` files that enforce this decision (e.g., build-feature.prompt.md)
- `AGENTS.md` if this ADR establishes a new convention for all code

Use the format: `See [ADR-XXX](../design/adr/XXX-kebab-case.md) for the full decision context.`

### 5. Create a Pull Request

1. Create a branch: `adr/NNN-decision-title`
2. Include the new ADR file and all updated documentation files in the PR.
3. Link to any related GitHub issue in the PR description: `Closes #XYZ` or `Relates to #XYZ`
4. Get review from at least two senior engineers.
5. Once approved, merge and change the ADR status from `Proposed` to `Accepted`.

## Examples of High-Quality ADRs in ClickNBack

Reference these for structure and style:

- [ADR 001: Adopt Modular Monolith](../../docs/design/adr/001-adopt-modular-monolith-approach.md) — excellent context, clear option comparison, honest tradeoffs
- [ADR 010: Async Database Layer](../../docs/design/adr/010-async-database-layer.md) — concrete code examples, clear consequences for new code
- [ADR 016: Background Job Pattern](../../docs/design/adr/016-background-job-architecture-pattern.md) — establishes a reusable pattern; well-documented consequences
- [ADR 023: Event-Driven Audit Logging](../../docs/design/adr/023-event-driven-audit-logging.md) — decision built on prior ADRs; clear tradeoffs and future considerations

## Common Pitfalls to Avoid

| Pitfall | Problem | How to Avoid |
| --- | --- | --- |
| **Decision is too local** | "Use this library in this one module" | Ask: "Does this precedent guide work across multiple modules?" If no, it's not an ADR. |
| **Insufficient context** | "We chose async because it's faster" — no tradeoff acknowledged | Explain what you gave up with explicit pros/cons. |
| **No real alternatives** | Only one option considered | Ask: "What would the opposite choice look like?" If there's no real alternative, you might not need an ADR. |
| **Vague title** | "Architectural Improvements" — hard to find or reference | Use concrete, searchable titles: "Use Persistent Audit Trail for Critical Operations" |
| **Decision not actionable** | "We should think about scalability" | State explicit, concrete decision: "New modules use `AsyncSession` to support concurrent DB access." |
| **ADR created but index not updated** | Decision exists but is undiscoverable | Update `docs/design/adr-index.md` immediately after creating the ADR file. |
| **ADR created but not linked from relevant docs** | Decision made but developers don't know about it | Link from guidelines, prompts, and AGENTS.md if it establishes a precedent. |

## Checklist

After writing your ADR:

- [ ] File created in `docs/design/adr/NNN-kebab-case-title.md`
- [ ] Status set to `Proposed`
- [ ] All sections filled in (Context with options, Decision, Consequences)
- [ ] Context is concrete; code examples or scenarios included where relevant
- [ ] Tradeoffs are explicit; both pros and cons listed for each option
- [ ] Consequences section covers: easier/harder, enforcement needed, reversibility
- [ ] Length is 500–800 words (not too short, not too long)
- [ ] Markdown formatting follows `docs/guidelines/markdown-docs.md` rules
- [ ] Related ADRs are referenced in the Consequences section
- [ ] **Entry added to `docs/design/adr-index.md` in numerical order**
- [ ] Related docs (`docs/guidelines/*.md`, `.github/prompts/*.md`, `AGENTS.md`) updated with links to the new ADR
