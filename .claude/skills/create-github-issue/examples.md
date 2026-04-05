---
name: create-github-issue-examples
type: examples
description: Real examples from ClickNBack repository showing properly formatted GitHub issues
---

# GitHub Issue Examples

All 15 examples below follow the Technical Task template and demonstrate proper title format, labeling, and content organization.

---

## Example 1: Feature Issue — Critical Priority

**Issue #72:** `[TASK] Add JWT refresh token support`

**Labels:** `type:task`, `priority:critical`, `phase:authentication`, `effort:high`

**Key Features:**
- Title: Clear, specific (3 words after prefix)
- Problem: User pain point (re-auth every 15 min)
- Solution: High-level (refresh token + rotation, no implementation details)
- Acceptance: 6 testable criteria (endpoint, single-use, error codes, TTL, concurrency)
- QA: Full checklist including API contracts, tests, migrations
- Notes: Effort estimate (5 days), blockers identified

```markdown
## Problem Statement

iOS apps must re-authenticate every 15 minutes due to lack of refresh token support, 
forcing users to re-enter their password ~4x per hour. This breaks the mobile UX and 
blocks iOS app adoption.

## Solution Overview

Add JWT refresh token support with server-side token rotation to enable long-lived 
sessions (30+ days) while maintaining security. Implement single-use token rotation 
and optional token revocation list.

## Acceptance Criteria

- [ ] POST /auth/refresh endpoint accepts refresh_token and returns new access_token + new refresh_token
- [ ] Refresh tokens cannot be reused after first use (single-use rotation enforced)
- [ ] Expired refresh token returns 401 INVALID_REFRESH_TOKEN
- [ ] Refresh token TTL configurable via settings (default: 30 days)
- [ ] Access token remains short-lived (15 min default)
- [ ] Concurrent refresh requests handled without race conditions

## Quality Assurance Checklist

- [ ] API contracts created/updated in `docs/design/api-contracts/auth/`
- [ ] HTTP test file created/updated in `http/auth/`
- [ ] Unit tests written and passing (`make test` reaches 85% coverage)
- [ ] Integration tests written and passing (`make test-integration`)
- [ ] Database migrations created and tested (if applicable)
- [ ] Docstrings/comments added
- [ ] Related ADRs or guidelines updated

## Implementation Notes

**Related:** Blocks iOS app development (Issue #XX)
**Follows:** ADR-008 (JWT auth pattern)
**Effort:** ~5 days (auth, DB, tests, API, docs)
```

---

## Example 2: Feature Issue — High Priority, Medium Effort

**Issue #76:** `[TASK] Add logout endpoint with server-side token invalidation`

**Labels:** `type:task`, `priority:high`, `phase:authentication`, `effort:medium`

**Key Features:**
- Title: Clear action verb (Add)
- Problem: Specific security concern (shared devices)
- Solution: Concise (logout revokes token)
- Acceptance: 5 testable criteria (endpoint, revocation, error responses)
- Notes: Depends on earlier issue (#73)

```markdown
## Problem Statement

Apps have no way to invalidate tokens on logout. Users believe they're logged out 
locally, but their tokens remain valid server-side. This is a security concern for 
shared devices.

## Solution Overview

Add POST /auth/logout endpoint that revokes the user's refresh token (and optionally 
current access token). Implement token revocation list in memory or database.

## Acceptance Criteria

- [ ] POST /auth/logout endpoint requires Authorization header
- [ ] Logout revokes the refresh token (cannot use it again)
- [ ] Logout returns 200 OK
- [ ] Subsequent requests with revoked token return 401 TOKEN_REVOKED
- [ ] Optional: logout_all_devices flag revokes all tokens for user

## Quality Assurance Checklist

- [ ] API contract created in `docs/design/api-contracts/auth/logout.md`
- [ ] HTTP test file created in `http/auth/logout.http`
- [ ] Unit tests for token revocation logic
- [ ] Integration tests verify token is truly invalid after logout
- [ ] Security audit: verify token revocation is atomic

## Implementation Notes

**Related:** Depends on #XX (token error codes)
**Effort:** ~3 days (revocation list, DB/cache updates, tests)
```

---

## Example 3: Standardization Issue — Critical, High Effort

**Issue #74:** `[TASK] Standardize pagination to offset/limit across all list endpoints`

**Labels:** `type:task`, `priority:critical`, `phase:standardization`, `effort:high`

**Key Features:**
- Affects 30+ endpoints across 7 modules
- Problem: Inconsistency prevents reusable app code
- Solution: Standard parameters + format
- Acceptance: Clear criteria for consistency
- Notes: Multi-module effort tracked

```markdown
## Problem Statement

List endpoints use inconsistent pagination schemes (page/page_size on some, 
offset/limit on others). Apps must implement multiple pagination patterns, 
increasing complexity. Offset/limit is mobile-friendly and supports cursor-based pagination.

## Solution Overview

Standardize all list endpoints to use offset/limit query parameters. Implement 
consistent pagination response format: `{ data: [...], pagination: { offset, limit, total } }`.

## Acceptance Criteria

- [ ] All GET /*/list endpoints accept offset and limit query parameters
- [ ] All list responses include pagination metadata (offset, limit, total)
- [ ] Default limit is 20, max is 100
- [ ] Offset defaults to 0
- [ ] Invalid offset/limit values return 422 with specific validation errors
- [ ] Old page/page_size parameters removed with deprecation notice

## Quality Assurance Checklist

- [ ] API contracts updated for all list endpoints (30+)
- [ ] HTTP test file updated with offset/limit examples
- [ ] Migration guide created for app developers
- [ ] Unit tests updated to use new pagination
- [ ] Integration tests verify pagination works across all modules

## Implementation Notes

**Related:** Requires updates across all modules (purchases, users, merchants, offers, 
payouts, wallets, feature_flags)
**Effort:** ~4 days (updates across 7 modules, migration guide)
```

---

## Example 4: Documentation Issue — Low Effort

**Issue #81:** `[DOCS] Document API versioning strategy and versions supported`

**Labels:** `type:task`, `priority:medium`, `phase:documentation`, `effort:low`

**Key Features:**
- Title: Clear outcome (Document)
- Problem: Uncertainty for app developers
- Solution: Policy document + support timeline
- Acceptance: Doc location, accessibility
- Notes: Low effort, documentation-only

```markdown
## Problem Statement

API versioning strategy is unclear. Apps don't know which API versions are 
supported, when they'll be deprecated, or how to handle breaking changes. This 
creates uncertainty for long-term app maintenance.

## Solution Overview

Document versioning strategy in README and API documentation:
- Semantic versioning (v1, v2, v3)
- 12-month deprecation notice before breaking changes
- Current version: v1 (stable)
- Sunset deadline for old versions
- Migration guide on breaking changes

## Acceptance Criteria

- [ ] API versioning policy documented in `docs/design/api-versioning.md`
- [ ] README explains versioning and support timeline
- [ ] API contract includes version information
- [ ] All breaking changes include migration guide
- [ ] Deprecation notices published 12 months in advance

## Quality Assurance Checklist

- [ ] Documentation is clear and accessible
- [ ] Versioning policy shared with all app developers
- [ ] Internal ADR created documenting decision (ADR-024: API Versioning)

## Implementation Notes

**Related:** Documentation phase
**Effort:** ~1 day (documentation only, no code changes)
```

---

## Example 5: Bug Fix Example Template

**Hypothetical Example:** `[BUG] Fix race condition in wallet withdrawals`

**Labels:** `type:bug`, `priority:critical`, `phase:accounts`

```markdown
## Problem Statement

During concurrent withdrawal requests, wallet balance can go negative. Two requests 
both read the same balance, both approve withdrawals exceeding available funds. Users 
can overdraw their wallets (financial risk).

Reproduction:
1. User has wallet with $50 available
2. Submit two concurrent withdrawal requests for $40 each
3. Both approve (total $80 withdrawn, balance = -$30)

## Solution Overview

Use SELECT FOR UPDATE row-level locking on wallet balance before checking sufficiency. 
This prevents concurrent reads from seeing stale balance state.

## Acceptance Criteria

- [ ] Concurrent withdrawal requests are serialized (one at a time)
- [ ] First request succeeds, second fails with INSUFFICIENT_FUNDS
- [ ] No wallet balance can go negative
- [ ] Load test: 100 concurrent requests block correctly

## Quality Assurance Checklist

- [ ] Root cause identified: missing row-level lock
- [ ] Fix implemented with SELECT FOR UPDATE
- [ ] Regression test added (concurrent withdrawals)
- [ ] Integration tests verify atomicity
- [ ] Performance: no noticeable latency increase

## Implementation Notes

**Root Cause:** Missing row-level locking on wallet query  
**Severity:** Critical (financial data corruption)  
**Related:** ADR-021 (Unit of Work pattern) — verify UoW implementation  
**Affected Users:** Any with concurrent withdrawals
```

---

## Quick Reference: Issue Naming Patterns

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `[TASK] Verb + noun` | `[TASK] Add JWT refresh token support` |
| Bug | `[BUG] Fix + problem` | `[BUG] Fix race condition in wallet withdrawals` |
| Refactor | `[REFACTOR] Reorganize/split + module` | `[REFACTOR] Split services.py into services/ package` |
| Docs | `[DOCS] Document + topic` | `[DOCS] Document API versioning strategy` |
| Performance | `[PERF] Optimize + operation` | `[PERF] Optimize list endpoint queries` |
| Security | `[SECURITY] Implement + control` | `[SECURITY] Implement rate limiting on auth` |

---

## Common Mistakes to Avoid

### ❌ Bad: Vague title
```
[TASK] Fix auth issues
[BUG] Something broken
[DOCS] Update stuff
```

### ✅ Good: Specific title
```
[TASK] Add JWT refresh token support
[BUG] Fix race condition in wallet withdrawals
[DOCS] Document API versioning strategy
```

---

### ❌ Bad: Implementation details in solution
```
## Solution Overview

Modify auth/services.py AuthService.refresh_token() method to check token 
revocation list in cache. Add new column token_revocation_id to auth_tokens table. 
Update TokenValidator class to...
```

### ✅ Good: High-level solution
```
## Solution Overview

Add JWT refresh token support with server-side token rotation to enable 
long-lived sessions. Implement single-use token rotation.
```

---

### ❌ Bad: Unmeasurable acceptance criteria
```
## Acceptance Criteria

- [ ] Token refresh works
- [ ] Security is good
- [ ] No bugs
```

### ✅ Good: Testable, measurable criteria
```
## Acceptance Criteria

- [ ] POST /auth/refresh accepts refresh_token and returns new access_token
- [ ] Refresh tokens cannot be reused after first use (single-use rotation)
- [ ] Expired refresh token returns 401 INVALID_REFRESH_TOKEN
- [ ] Concurrent refresh requests handled without race conditions
```

---

## Creating Issues Programmatically

### Using GitHub CLI

```bash
#!/bin/bash
# Create a feature issue

gh issue create \
  --title "[TASK] Add JWT refresh token support" \
  --body "$(cat << 'EOF'
## Problem Statement

iOS apps must re-authenticate every 15 minutes...

## Solution Overview

Add JWT refresh token support...

## Acceptance Criteria

- [ ] POST /auth/refresh accepts refresh_token...
EOF
)" \
  --label "type:task,priority:critical,phase:authentication,effort:high"
```

### Using MCP GitHub Tools (from VS Code)

```python
# See index.md for workflow and label taxonomy
mcp_io_github_git_issue_write(
    method="create",
    owner="jerosanchez",
    repo="clicknback",
    title="[TASK] Add JWT refresh token support",
    body="...(formatted problem statement, solution, criteria, checklist)...",
    labels=["type:task", "priority:critical", "phase:authentication", "effort:high"]
)
```

---
