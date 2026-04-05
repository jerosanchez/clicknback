---
name: create-github-issue-template
type: template
description: Issue template stubs for different issue types following ClickNBack standards
---

# GitHub Issue Templates

## Feature Issue Template

```markdown
## Problem Statement

<!-- Why are we solving this? What's the business impact? -->

## Solution Overview

<!-- What are we building? (high-level, no implementation details) -->

## Acceptance Criteria

<!-- How do we verify this is done? Make it testable. -->
- [ ] 
- [ ] 
- [ ] 

## Quality Assurance Checklist

- [ ] API contracts created/updated in `docs/design/api-contracts/`
- [ ] HTTP test file created/updated in `http/<module>/`
- [ ] Unit tests written and passing (`make test` reaches 85% coverage)
- [ ] Integration tests written and passing (`make test-integration`)
- [ ] Database migrations created and tested (if applicable)
- [ ] Docstrings/comments added
- [ ] Related ADRs or guidelines updated (if architectural decision made)

## Implementation Notes

**Phase:** [authentication|standardization|accounts|documentation|observability|security|payouts]  
**Effort:** [low|medium|high|critical]  
**Related Issues:** #XX, #YY  
**Key Context:** ...
```

---

## When to Merge vs. Split Issues

**MERGE into ONE issue if:**
- All work is in the same module
- Features are tightly coupled (one depends on the other sequentially)
- Can't deploy separately without breaking things
- Total effort < 5 days

Example: User registration (models → repo → service → API) — all related, one issue

**SPLIT into MULTIPLE issues if:**
- Clear separation of concerns (different modules/responsibilities)
- Can be deployed independently
- Different teams could work on them in parallel
- One doesn't require the other to function

Example: Wallet extension (+1 issue) then payouts using wallet client (+1 issue)

```markdown
## Problem Statement

<!-- What is broken? What's the user/system impact? -->

## Solution Overview

<!-- How are we fixing it? (high-level approach) -->

## Acceptance Criteria

<!-- How do we verify the bug is fixed? -->
- [ ] Bug scenario is no longer reproducible
- [ ] Regression test added
- [ ] Root cause documented

## Quality Assurance Checklist

- [ ] Root cause identified and documented
- [ ] Fix implemented
- [ ] Unit tests added (test the fix)
- [ ] Integration tests added (verify fix doesn't break other code)
- [ ] Manual testing completed
- [ ] Docstrings updated if behavior changed

## Implementation Notes

**Root Cause:** ...  
**Phase:** bugfix  
**Effort:** [low|medium|high]  
**Related Issues:** #XX (original report)
```

---

## Refactoring Issue Template

```markdown
## Problem Statement

<!-- Why does the code need refactoring? What problem does it solve? -->
<!-- Examples: "Module is > 500 lines (hard to navigate)", "10+ similar functions (DRY violation)", etc." -->

## Solution Overview

<!-- How are we refactoring? (high-level approach) -->
<!-- Example: "Split services.py into services/ package with separate classes per operation type" -->

## Acceptance Criteria

- [ ] Refactored code maintains 100% test coverage
- [ ] No behavior changes (same inputs → same outputs)
- [ ] Code navigation/readability improved
- [ ] No new linting or security issues

## Quality Assurance Checklist

- [ ] All existing tests still pass
- [ ] No new issues reported by `make lint` or `make security`
- [ ] Code review confirms design is sound
- [ ] Performance benchmarks show no regression (if applicable)

## Implementation Notes

**Phase:** technical-debt  
**Effort:** [low|medium|high]  
**Non-Breaking:** Yes (refactors should never change API)  
**Motivation:** ...
```

---

## Documentation Issue Template

```markdown
## Problem Statement

<!-- What documentation is missing or unclear? What's the impact? -->

## Solution Overview

<!-- What are we documenting? Where will it live? -->

## Acceptance Criteria

- [ ] Documentation created/updated at [path]
- [ ] Examples provided
- [ ] Clear and accessible for target audience (developers|product managers|PMs)
- [ ] Linked from related docs/ADRs

## Quality Assurance Checklist

- [ ] Markdown linting passes (`make lint`)
- [ ] Links are valid and functional
- [ ] Examples are tested/realistic
- [ ] No typos or grammar issues
- [ ] Consistent with documentation standards

## Implementation Notes

**Audience:** [developers|product|qa|all]  
**Phase:** documentation  
**Effort:** low  
**Doc Location:** [path/to/docs/]
```

---

## Performance Issue Template

```markdown
## Problem Statement

<!-- What's slow? What's the impact? Include metrics if available. -->
<!-- Example: "List purchases endpoint takes 5+ seconds with 10k+ purchases; user experience is poor" -->

## Solution Overview

<!-- How are we optimizing? (high-level approach) -->
<!-- Example: "Add database indices on user_id and created_at; implement offset/limit pagination" -->

## Acceptance Criteria

- [ ] Operation is < [target time] (e.g., 200ms for list endpoint)
- [ ] Load test shows [target throughput] (e.g., 1000 requests/sec)
- [ ] No SQL queries with N+1 problems
- [ ] Memory usage does not increase

## Quality Assurance Checklist

- [ ] Benchmarks collected (before/after)
- [ ] Load testing completed
- [ ] Profiling shows bottleneck eliminated
- [ ] No regression in other operations

## Implementation Notes

**Phase:** performance  
**Effort:** [medium|high]  
**Metrics:** [current performance] → [target performance]  
**Bottleneck:** [identified slow operation]
```

---

## Security Issue Template

```markdown
## Problem Statement

<!-- What's the security vulnerability or risk? -->
<!-- Example: "Auth endpoints have no rate limiting; vulnerable to brute force attacks" -->

## Solution Overview

<!-- How are we addressing the security issue? -->
<!-- Example: "Implement rate limiting: max 5 login attempts per minute per IP" -->

## Acceptance Criteria

- [ ] Vulnerability is mitigated/fixed
- [ ] Security review approved by team
- [ ] No new security warnings from `make security`
- [ ] Monitoring/alerting in place (if needed)

## Quality Assurance Checklist

- [ ] Security audit completed
- [ ] OWASP guidelines reviewed (if applicable)
- [ ] Bandit security check passes
- [ ] Penetration testing (if high-risk change)

## Implementation Notes

**Phase:** security  
**Effort:** [low|medium|high]  
**Risk Level:** [low|medium|high|critical]  
**CVSS Score:** [if applicable]  
**Related CVE:** [if applicable]
```

---

## Labels Reference

### Type Labels (Required)
- `type:task` — Feature implementation
- `type:bug` — Bug fix
- `type:refactor` — Code refactoring
- `type:perf` — Performance improvement
- `type:docs` — Documentation
- `type:security` — Security improvement

### Priority Labels (Optional)
- `priority:critical` — Blocks other work; high impact
- `priority:high` — Important; should happen soon
- `priority:medium` — Nice to have; can be deferred
- `priority:low` — Deprioritizable

### Phase Labels (Optional)
- `phase:authentication` — Auth features
- `phase:standardization` — API standardization
- `phase:accounts` — Account management
- `phase:observability` — Observability/tracing
- `phase:security` — Security hardening
- `phase:documentation` — Docs/guides
- `phase:app-management` — App versioning
- `phase:payouts` — Payouts features
- `phase:performance` — Performance
- `phase:technical-debt` — Tech debt/refactoring

### Effort Labels (Optional)
- `effort:low` — < 1 day
- `effort:medium` — 1-3 days
- `effort:high` — 3-5 days
- `effort:critical` — 5+ days

---
