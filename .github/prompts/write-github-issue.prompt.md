# Prompt: Write a GitHub Issue

Use this prompt to draft a detailed GitHub issue in Markdown format that is ready to copy/paste into GitHub. Follow this template to ensure consistency, clarity, and actionability.

## Context

- Read `docs/guidelines/markdown-docs.md` for all Markdown formatting, heading levels, code block conventions, and whitespace rules.
- Each issue must follow the structure below: Summary, Problem Statement, Proposed Solution, Implementation Plan, Acceptance Criteria, Related Documentation, Out of Scope, and Notes.
- Use task lists (`- [ ]`) for concrete steps in the Implementation Plan and Acceptance Criteria sections.
- Ensure every heading has exactly one blank line before and after; no trailing punctuation in headings.
- Code blocks and commands must be fenced and include a language tag.
- One line per paragraph, no manual wrapping (let the editor handle line breaks).

## Issue Template Structure

### 1. Title

One-line summary of the issue, written as an imperative verb + noun phrase (e.g., "Refactor Audit Logging to Use Event-Driven Model").

### 2. Summary

One paragraph (3–5 sentences) explaining what this issue is about, why it matters, and what the expected outcome is. Lead with the problem or opportunity, not the solution.

```markdown
# Refactor Audit Logging to Use Event-Driven Model

## Summary

The audit logging system currently requires direct injection of the `AuditTrail` service into every service, job, and handler that performs critical operations. This creates unnecessary coupling between business logic and audit infrastructure, obscures business logic with audit record construction, and limits audit logging scalability. Extract audit logging to an independent, event-driven module that subscribes to domain events published via the message broker. This decouples audit logic from business logic, prepares the codebase for future async/distributed audit processing, and aligns with the modular monolith architecture.
```

### 3. Problem Statement

Describe the current state with concrete evidence. Include subsections:

- **Current Implementation:** How is the system working today? Include code examples, class names, file paths, or architectural details.
- **Consequences:** What are the negative impacts? List coupling issues, scalability concerns, testability problems, or future risks.

```markdown
## Problem Statement

### Current Implementation

- `AuditTrail` service is injected as a dependency into `PurchaseService`, verification job tasks, and job processors.
- After each critical operation, service methods call `audit_trail.record(...)` with manually constructed audit details.
- Audit record construction is scattered throughout the codebase and intermingled with business logic.

### Consequences

- **Coupling:** Audit becomes a cross-cutting concern polluting service signatures and constructor code.
- **Scalability:** As more operations require audit logging, the number of injections and calls grows linearly.
- **Testability:** Services must mock the audit service in every test; audit calls clutter test assertions.
```

### 4. Proposed Solution

Outline the high-level strategy and benefits. Include subsections:

- **Architecture:** How will the new system work? Describe the flow, components, and interactions.
- **Benefits:** What problems does this solve? List concrete improvements.

```markdown
## Proposed Solution

### Architecture

1. **Define Audit Events:** Create event classes that capture the semantic details of each auditable operation.
2. **Audit Subscriber:** Implement an event handler that subscribes to audit events via the broker and writes records asynchronously.
3. **Remove Audit Injections:** Delete the `audit_trail` parameter from all service constructors.
4. **Emit Events Instead:** Replace all audit calls with event emissions.

### Benefits

- **Clean separation:** Business logic no longer constructs or calls audit record logic.
- **Event-driven architecture:** Audit is just one subscriber; new subscribers can be added without touching business logic.
- **Future-proof:** Audit handler can be moved to a microservice without touching consumer code.
```

### 5. Implementation Plan

Break the work into phased, sequential steps. Each phase should be labeled and include a numbered or task-list breakdown of concrete actions. Use task lists (`- [ ]`) so progress can be tracked directly in GitHub.

```markdown
## Implementation Plan

### Phase 1 — Event Definition

- [ ] Review all current audit calls across the codebase.
- [ ] Create audit event classes in `app/core/events/audit_events.py`.
- [ ] Document each event's semantic meaning.

### Phase 2 — Audit Handler Implementation

- [ ] Create `app/core/audit/handlers.py` with an async event handler.
- [ ] Update composition to export subscription function.
- [ ] Add logging to track audit record creation.
```

### 6. Acceptance Criteria

List the testable, measurable conditions that define "done". Use task lists so progress is visible in GitHub.

```markdown
## Acceptance Criteria

- [ ] All audit service injections are removed from service and job code.
- [ ] All audit record calls are replaced with event emissions.
- [ ] Tests verify each audit event triggers an audit record.
- [ ] Full test suite passes with 85%+ coverage.
- [ ] All linting gates pass (`markdownlint`, `flake8`, `isort`, `black`, `bandit`).
- [ ] Documentation is updated with new ADR and event definitions.
```

### 7. Related Documentation

List relevant files, ADRs, guidelines, or specifications that provide context. Format as bullet points with file paths and brief descriptions.

```markdown
## Related Documentation

- `AGENTS.md` — section on audit logging (current implementation).
- `docs/design/adr/015-audit-trail-recording.md` — current audit architecture.
- `docs/guidelines/background-jobs.md` — event emission in job runners.
```

### 8. Out of Scope

Specify what this issue does NOT cover. This prevents scope creep and clarifies expectations.

```markdown
## Out of Scope

- Changing the audit table schema or renaming fields.
- Moving audit to an external service (future work).
- Implementing distributed tracing or spans (orthogonal concern).
```

### 9. Notes

Any additional context, assumptions, trade-offs, or helpful guidance. This section is optional but valuable for long-term maintenance.

```markdown
## Notes

- This refactoring is backward-compatible from an external API perspective; no HTTP contracts change.
- The broker is already present and used for other events; no new infrastructure changes required.
- Event handler execution is sequential; audit writes are synchronous within the transaction.
```

---

## Writing Guidelines

### Language and Tone

- Use imperative voice for action items ("Create," "Remove," "Update").
- Use clear, technical language appropriate for the engineering team.
- Avoid ambiguous pronouns or vague terms like "fix," "improve," or "optimize" without context.
- Lead every section with a one-sentence statement of what and why before diving into how.

### Formatting

- One paragraph per logical idea; no manual line wrapping mid-paragraph.
- Every code reference (file path, class name, function name, config key) must be in inline code (e.g., `` `AuditTrail` ``).
- Code blocks must be fenced with triple backticks and include a language tag (e.g., ` ```markdown `).
- Use bold (`**term**`) for section labels within lists or tables; end with a colon if not a heading.
- Use task lists (`- [ ]`) for steps that can be tracked as "done" in GitHub; use regular unordered lists (`-`) for non-actionable items.

### Headings

- Title (top level, `#`): One per file; write as imperative phrase.
- Sections (`##`): Major logical blocks (Summary, Problem Statement, Proposed Solution, etc.).
- Subsections (`###`): Details within a section (e.g., "Architecture," "Current Implementation," "Phase 1").
- Sub-subsections (`####`): Use sparingly; prefer restructuring if more than 3 levels needed.

### Linking

- Always link to relevant files, ADRs, and documentation in the "Related Documentation" section.
- Use relative paths and format as `[display-text](path/to/file.md)`.
- Never hardcode absolute paths or URLs unless referring to external resources.

### Task Lists

- Use `- [ ]` for items to be tracked as "done"; GitHub will allow checking them off.
- Use `- [ ] **Subsection Title:** description` to group related tasks under a bold label.
- Ensure every task is specific and measurable; avoid vague tasks like "test everything."

## Example Structure (Condensed)

```markdown
# [Imperative Title]

## Summary

[1–2 sentences leading with problem or opportunity; 1–2 sentences explaining the solution and why it matters.]

## Problem Statement

### Current Implementation

[What exists today; include file paths and code hints.]

### Consequences

[Negative impacts grouped by concern (coupling, scalability, testability, etc.).]

## Proposed Solution

### Architecture

[How will the new system work; describe flow and components.]

### Benefits

[Concrete improvements; avoid generic phrases.]

## Implementation Plan

### Phase 1 — [Phase Title]

- [ ] Task 1
- [ ] Task 2

### Phase 2 — [Phase Title]

- [ ] Task 1
- [ ] Task 2

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Related Documentation

- [Description](path/to/file.md)

## Out of Scope

- Item 1

## Notes

[Optional; any additional context or trade-offs.]
```

---

## GitHub MCP Tools Integration

When using the GitHub MCP server, the following tools are available for issue management:

- `mcp_io_github_git_issue_write()` — Create or update a single issue with title, body, labels, assignees, and milestone.
- `mcp_io_github_git_search_issues()` — Search for existing issues before creating a new one (useful to avoid duplicates).
- `mcp_io_github_git_issue_read()` — Fetch details of a specific issue.
- `mcp_io_github_git_add_issue_comment()` — Add a comment to an existing issue (useful for updates or progress notes).
- `mcp_io_github_git_sub_issue_write()` — Add sub-issues to a parent issue to break down work.

Before creating a new issue, consider searching for similar issues first to avoid duplicates:

```bash
mcp_io_github_git_search_issues(
    query="Audit Logging event-driven",
    owner="jerosanchez",
    repo="clicknback"
)
```

---

- **Vague problem statement:** Anchor the problem in concrete code and file paths; do not assume readers have domain knowledge.
- **Solution without context:** Explain why the solution is better; do not just list steps.
- **Unclear acceptance criteria:** Each criterion must be testable and measurable; avoid subjective language like "good performance" or "clean code."
- **Mixing concerns across phases:** Each phase should be completable independently; do not create circular dependencies.
- **Missing related documentation:** Always link to relevant ADRs, specs, and guidelines; readers should not have to hunt for context.
- **Scope creep:** Use "Out of Scope" liberally to prevent the issue from ballooning; keep it focused on one atomic concern.

---

## Usage

### Option 1 — Manual (Copy/Paste to GitHub)

1. Copy this template structure into a markdown file.
2. Fill in each section with details specific to your issue.
3. Follow all Markdown formatting rules from `docs/guidelines/markdown-docs.md`.
4. Validate the final output with `markdownlint` to ensure zero linting errors.
5. Copy the entire content (minus this prompt header) and paste it directly into a new GitHub issue.

### Option 2 — Automatic (Using GitHub MCP Server) — Recommended

If you have the GitHub MCP server installed, you can create the issue automatically in one step:

1. Fill in all sections of the prompt using the template structure above.
2. Run the GitHub MCP tool to create the issue:
   - Provide the issue **title** (from the markdown `#` heading).
   - Provide the **body** (all content from `##` Summary onward).
   - Optionally add **labels** (e.g., `["architecture", "refactoring", "enhancement"]`).
   - Specify **owner** (repository owner) and **repo** (repository name).
3. The tool will create the issue in GitHub immediately and return the issue URL.
4. **Do not leave a local draft file in the repo** — once the issue is created on GitHub, it is the single source of truth. Discard any temporary working file.

This approach bypasses manual copy/paste and integrates issue creation directly into your workflow. Example:

```bash
# Via the MCP tool interface
mcp_io_github_git_issue_write(
    method="create",
    owner="jerosanchez",
    repo="clicknback",
    title="Refactor Audit Logging to Use Event-Driven Model",
    body="[full markdown content from ## Summary onward]",
    labels=["architecture", "refactoring", "audit", "event-driven"]
)
```

After creation, delete any local draft files to keep the repository clean.
