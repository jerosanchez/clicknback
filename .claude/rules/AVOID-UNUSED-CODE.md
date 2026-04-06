---
name: avoid-unused-code
type: rule
description: Guidance on not implementing unused code and reporting possible improvements instead
---

# AVOID-UNUSED-CODE

## Principle

**Do not implement code that is not immediately required or actively used.** Unused code creates technical debt, clutters the codebase, complicates testing, and obscures intent. If a feature is desirable for the future but not currently needed, document it as a GitHub issue with the reasoning instead.

## When Code is "Unused"

Code is unused when:

- ✅ It's defined but never called anywhere in the codebase
- ✅ It's in a repository or service interface but not invoked by any business flow
- ✅ It's been deprecated or superseded and no longer serves a purpose
- ✅ It was written "just in case" for a future feature that hasn't materialized

**Early signals:**
- Lint rules do not flag it as unused (Python's analyzer would not catch this, but manual inspection reveals no call sites)
- Tests don't exercise it (no direct tests, no integration tests that require it)
- Search across the codebase returns zero results for its invocation

## Action: Remove Unused Code

1. **Confirm it's truly unused** — `grep_search` the codebase to verify zero call sites
2. **Remove it** from both abstract interface (ABC) and concrete implementation
3. **Run all quality gates** — `make all-qa-gates` must pass with zero failures
4. **Document the removal** in the commit message if committing directly

## Action: Report as Improvement

When you discover desired functionality that is unused:

1. **Do NOT implement it preemptively**
2. **Create a GitHub issue** with:
   - **Title format**: `[TASK] <Feature Description>` (e.g., `[TASK] Add background job to clean up expired tokens`)
   - **Problem Statement**: Why is this valuable? (performance, compliance, maintenance, etc.)
   - **Solution Overview**: High-level approach (not implementation details)
   - **Acceptance Criteria**: 4-8 testable conditions
   - **Quality Gate Checklist**: Standard items (tests, lint, security, docs)
   - **Effort Estimate**: Use `effort:` label (low, medium, high, critical)
   - **Priority**: Use `priority:` label (critical, high, medium, low)

3. **Link related context** — reference ADRs, existing code, or design patterns
4. **The human decides** — they can create a milestone, assign it, or discard it

### Example: Unused `delete_expired` Method

**What we found:**
- `RefreshTokenRepositoryABC.delete_expired()` is defined but never called
- No tests exercise it; no service method uses it

**What we did:**
- ✅ Removed the method from both abstract and concrete implementations
- ✅ Ran `make all-qa-gates` — 89% coverage, all tests pass
- ✅ Created GitHub issue #92 with full context, suggesting implementation as a background job
- ✅ Added this guidance to Claude docs

**Why this is better:**
- Codebase stays lean; only implements what's actively used
- Future maintainers won't wonder if the method is dead code
- If the feature is truly needed later, the issue documents the reasoning and best practices for implementation

---

## Code Smell Checklist

Before implementing a new method or function, ask:

- [ ] Is there an immediate call site or business flow that requires this?
- [ ] Do we have acceptance criteria that exercise this code?
- [ ] Is there a test that covers this?
- [ ] If removed tomorrow, would anything break?

**If all answers are NO** — it's a candidate for postponement. Create an issue instead.

---

## Update Claude Instructions

When removing unused code, update:

1. **This rule** — Add examples and keep guidance current
2. **Relevant skill workflows** — E.g., build-feature, write-unit-tests (ensure we don't add unused features)
3. **CONTRIBUTING.md** (if public) — Add guidance about removing dead code in PRs

---

## References

- **Quality Gates**: [QUALITY-GATES.md](./QUALITY-GATES.md) — All quality gates must pass after code removal
- **GitHub Issue Workflow**: [GitHub Issue Skill](../.claude/skills/create-github-issue/index.md) — How to create issues with proper structure
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md) — Modular monolith keeps code intentional and bounded

---
