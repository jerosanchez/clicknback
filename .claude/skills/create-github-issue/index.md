---
name: create-github-issue
type: skill
description: Workflow for creating GitHub issues following ClickNBack standards using the technical task template
---

# Create GitHub Issue Skill

## Overview

This skill provides a systematic workflow for creating GitHub issues that follow ClickNBack standards. Issues are the primary communication tool for tracking features, bugs, and improvements. All issues must use the Technical Task template and follow consistent naming, labeling, and structure conventions.

**Related Documentation:**
- [AUTONOMOUS-EXECUTION.md](../../rules/AUTONOMOUS-EXECUTION.md) — When to create issues autonomously
- [PROJECT.md](../../rules/PROJECT.md) — Project context and domain knowledge

---

## Workflow

### 1. Gather Context
Before creating an issue, collect:
- **Problem/Feature:** What needs to be done? Why?
- **Business Impact:** How does this affect users or the platform?
- **Related Work:** Does this depend on other issues? Is it related to others?
- **Effort Estimate:** 1-2 days, 2-5 days, or 5+ days?
- **Phase/Category:** Which iteration/phase does this belong to?

### 2. Choose Issue Type & Title Format

**Format:** `[CONTEXT] Short description (3-7 words)`

| Type | Prefix | Example | Use When |
|------|--------|---------|----------|
| **Feature** | `[TASK]` | `[TASK] Add JWT refresh token support` | Implementing a new feature or endpoint |
| **Bug** | `[BUG]` | `[BUG] Fix race condition in wallet withdrawals` | Fixing broken behavior |
| **Refactor** | `[REFACTOR]` | `[REFACTOR] Reorganize auth module structure` | Improving code without changing behavior |
| **Performance** | `[PERF]` | `[PERF] Optimize list endpoint queries` | Making something faster |
| **Documentation** | `[DOCS]` | `[DOCS] Document API versioning policy` | Writing or updating docs |
| **Security** | `[SECURITY]` | `[SECURITY] Implement rate limiting on auth` | Security improvements or hardening |

### 3. Fill Template Sections

All issues must use the Technical Task template (`.github/ISSUE_TEMPLATES/technical-task.md`). Fill sections in order:

#### A. Problem Statement
- Answer: **Why are we solving this?**
- Include: Business impact, user pain point, blocked features
- Be concise but specific
- Link to related issues/ADRs if applicable

#### B. Solution Overview
- Answer: **What are we building?** (high-level)
- Do NOT specify implementation details (files, methods, architecture)
- Details will be discovered during implementation
- Example: "Add JWT refresh token support with server-side token rotation" (not "modify auth/services.py, add new table, etc.")

#### C. Acceptance Criteria
- Answer: **How do we verify this is done?**
- 4-8 testable conditions
- Start with empty checkboxes: `[ ]`
- One criterion per line
- Examples: API responses, error codes, concurrent scenarios, state transitions

#### D. Quality Assurance Checklist
- Pre-filled standard items:
  - API contracts created/updated
  - HTTP test file created/updated
  - Unit tests written and passing (85%+ coverage)
  - Integration tests passing
  - Database migrations (if applicable)
  - Docstrings/comments added
  - Related ADRs or guidelines updated

### 4. Assign Labels

**Required Labels:**
- `type:<type>` — `type:task`, `type:bug`, `type:refactor`, `type:perf`, `type:docs`, `type:security`

**Optional Priority:** (choose one)
- `priority:critical` — Blocks other work, security/financial risk
- `priority:high` — Important, should happen soon
- `priority:medium` — Nice to have, can be deferred
- `priority:low` — Nice to have, deprioritizable

**Optional Phase:** (choose one, optional)
- `phase:authentication` — Auth features
- `phase:standardization` — API standardization
- `phase:accounts` — Account management
- `phase:observability` — Logging, tracing, monitoring
- `phase:security` — Security hardening
- `phase:documentation` — Docs and guides
- `phase:app-management` — App version, lifecycle
- `phase:performance` — Performance improvements

**Optional Effort:** (choose one, optional)
- `effort:low` — < 1 day
- `effort:medium` — 1-3 days
- `effort:high` — 3-5 days
- `effort:critical` — 5+ days

### 5. Add Implementation Notes (Optional)

Include context that helps during implementation:
- "Follows ADR-008 (JWT auth pattern)"
- "Depends on #72 (JWT refresh token support)"
- "Related: Issue #42 (iOS app blocking)"
- "Coordinate with auth module changes"
- "Consider security implications for shared devices"

### 6. Create Issue

ClickNBack uses **GitHub MCP Server** (integrated with VS Code) as the primary method for creating issues programmatically.

**GitHub MCP Server (Recommended):**

Requires: GitHub MCP Server extension in VS Code

```python
# Claude uses mcp_io_github_git_issue_write() to create issues
mcp_io_github_git_issue_write(
    method="create",
    owner="jerosanchez",
    repo="clicknback",
    title="[TASK] Add JWT refresh token support",
    body="""## Problem Statement
...
## Solution Overview
...
## Acceptance Criteria
...
""",
    labels=["type:task", "priority:critical", "phase:authentication", "effort:high"]
)
```

**If GitHub MCP Server is not installed:**
1. Open VS Code Extensions (Cmd/Ctrl + Shift + X)
2. Search for "GitHub MCP Server"
3. Install the official GitHub extension
4. Authenticate with your GitHub account
5. Retry issue creation

**Alternative: Web Interface**
1. Visit https://github.com/jerosanchez/clicknback/issues
2. Click "New Issue"
3. Select "Technical Task" template
4. Fill in all sections
5. Add labels
6. Click "Create Issue"

**Alternative: GitHub CLI** (if `gh` is installed)
```bash
gh issue create \
  --title "[TASK] Add JWT refresh token support" \
  --body "$(cat issue_body.md)" \
  --label "type:task,priority:critical,phase:authentication,effort:high"
```

---

## Constraints & Rules

### ✅ DO

- Use the Technical Task template for all issues
- Include business impact in Problem Statement
- Write testable acceptance criteria (no vague goals)
- Estimate effort (helps with sprint planning)
- Link related issues in Implementation Notes
- Add phase/category labels for filtering
- Reference ADRs or guidelines when applicable

### ❌ DON'T

- Create issues with vague titles ("Fix bugs", "Improvements", "Auth stuff")
- Pre-solve the implementation in the issue
- Include specific file names/method names in Problem/Solution sections
- Leave Implementation Notes blank (at minimum: effort + phase)
- Create issues that depend on undocumented decisions
- Mix multiple unrelated tasks in one issue (split into separate issues)
- Leave acceptance criteria as adjectives ("Make it faster", "Handle errors")

---

## Validation Checklist

Before creating an issue, verify:

- [ ] **Title has consistent prefix** (`[TASK]`, `[BUG]`, etc.)
- [ ] **Title is 3-7 words** after prefix (not too vague, not too verbose)
- [ ] **Problem Statement is specific** (real impact, not hypothetical)
- [ ] **Solution Overview is high-level** (no implementation details)
- [ ] **4-8 acceptance criteria** (testable, specific)
- [ ] **Related issues linked** (dependencies documented)
- [ ] **Labels assigned** (at least `type:*`, optionally priority/phase/effort)
- [ ] **Implementation Notes included** (effort estimate, phase, related context)
- [ ] **Issue fits in one sprint** (if 5+ days, consider breaking into sub-issues)

---

## Phase Grouping & Timeline

Issues are organized into execution phases for sprint planning:

| Phase | Issues | Duration | Dependencies |
|-------|--------|----------|--------------|
| **Authentication** | #72-73, #76-79 | 2-3 weeks | None |
| **Standardization** | #74-75, #78 | 1-2 weeks | Completed Auth phase |
| **Accounts** | #80 | 1 week | Completed Auth phase |
| **Documentation** | #81-86 | 1 week | All phases (docs last) |

**Timeline:** 4-5 weeks total (phases overlap slightly with auth + standardization parallel)

---

## Examples

See [examples.md](./examples.md) for three fully worked-out examples:

1. **Feature Issue Example** — [TASK] Add JWT refresh token support
2. **Documentation Issue Example** — [DOCS] Document API versioning strategy
3. **Bug Fix Example** — [BUG] Fix race condition in wallet withdrawals

---

## When to Create Sub-Issues

If an issue exceeds ~5 days of effort, **consider splitting only if there's clear separation of concerns and each can be deployed independently** without breaking anything.

### Decision Framework

**Merge into ONE issue if:**
- All work is in the same module (e.g., `/app/payouts/`)
- Features are tightly coupled (one depends on the other)
- Can't deploy changes separately without breaking things
- Estimated effort < 5 days combined
- Example: User registration (models → repo → service → API) — all related, one issue

**Split into MULTIPLE issues if:**
- Clear separation of concerns (different responsibilities)
- Can be deployed independently without breaking changes
- Different teams could work on them in parallel
- One doesn't require the other to function
- Example (Payouts as separate concern):
  - **Issue 1:** `[TASK] Extend ledger module to support payout credits` (schema, repo new method)
  - **Issue 2:** `[TASK] Implement payout withdrawal via ledger client` (service, API endpoint using the new ledger method)
  - Reason: Ledger is separate module; extending it can ship first, then clients use it later

### Real Example: Payouts Feature

From ClickNBack backlog — three payouts features, analyzed as:

✅ **ONE issue:** Payout Withdrawal Request Creation (#88)
- All in `app/payouts/` module
- Models → Schemas → Repos → Services → API tightly coupled
- Can't separate implementation
- Effort: 3 days

✅ **ONE issue:** Payout Approval + Processing (#89)
- Admin endpoints + background job both in payouts
- Approval triggers job (workflow, not separation)
- Both deploy together
- Effort: 4 days

✅ **ONE issue:** Payout Listing (#87)
- Distinct, self-contained feature
- Can ship anytime after withdrawal requests exist
- Effort: 2 days

❌ **Would split if:** Extending wallet module first, then payouts uses wallet client
- Wallet extension = one issue (new repo method)
- Payouts implementation = another issue (uses wallet client)
- Can deploy separately without breaking anything

---
