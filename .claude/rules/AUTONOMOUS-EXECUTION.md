---
name: autonomous-execution
type: rule
description: Decision framework for when Claude runs commands autonomously vs. requires approval
---

# AUTONOMOUS-EXECUTION

**🤖 DIRECTIVE: Claude MUST use this rule to make autonomous execution decisions. Apply the decision framework below to every command without asking for permission unless explicitly listed in "Commands Requiring Explicit Approval".**

Claude in this project is configured to autonomously execute non-destructive commands and require explicit approval for destructive or high-risk operations.

## Makefile-First Principle

**Prefer Makefile targets over raw commands.** This project ships a `Makefile`; use it.

When a Makefile target does what you need, run `make <target>` — never invoke the underlying tool directly. This keeps behaviour consistent with how a human developer works and ensures shared environment configuration (flags, URLs, container names) is always applied correctly.

| Action | ✅ Use this | ❌ Not this |
|--------|------------|------------|
| Start dev environment | `make up` | `docker compose -f docker-compose.dev.yml up ...` |
| Stop dev environment | `make down` | `docker compose -f docker-compose.dev.yml down` |
| Reset database (drop + migrate + seed) | `make db-reset` | `alembic downgrade base && alembic upgrade head && psql ...` |
| Apply migrations only | `make migrate` | `alembic upgrade head` |
| Run app locally (hot-reload) | `make dev` | `uvicorn app.main:app --reload` |
| Tail container logs | `make logs` | `docker compose logs -f` |
| Run unit tests | `make test` | `pytest tests/unit/ ...` |
| Run integration tests | `make test-integration` | `pytest tests/integration/ ...` |
| Run E2E tests | `make test-e2e` | `pytest tests/e2e/ ...` |
| Check coverage grade | `make coverage` | `pytest ... && scripts/coverage-grade.sh` |
| Run linters | `make lint` | `flake8 ... && isort ... && black ...` |
| Security scan | `make security` | `bandit -r app/ ...` |
| Run ALL quality gates | `make all-qa-gates` | individual commands chained manually |

**Only use raw commands when no Makefile target exists** for the desired action.

## Quality Gate Workflow

Use a two-speed approach during development:

- **During development** (fast feedback loop): `make lint && make test && make coverage && make security`
- **Before finishing any task** (full gate): `make all-qa-gates`

`make all-qa-gates` runs lint → unit tests + coverage → security → integration tests → E2E tests in sequence.
Run it as the final check before declaring a task done. This mirrors what CI/CD pipelines execute and
catches failures that unit tests alone cannot catch (e.g. missing `uow.commit()`, broken HTTP routes).

## Test-Running Rules

When **adding, changing, or removing tests**:

| Action | Make target to run |
|--------|--------------------|
| Add/change/remove unit tests | `make test` |
| Add/change/remove integration tests | `make test-integration` |
| Add/change/remove E2E tests | `make test-e2e` |
| After completing any task | `make all-qa-gates` |

Never run `pytest` directly — always use the corresponding Makefile target so that the test database
lifecycle (spin up / tear down), environment variables, and coverage reporting are handled correctly.

## How Claude Uses This Rule

When a command is proposed:

1. Claude consults this decision framework first (before execution).
2. If the decision tree leads to "Execute autonomously" → Execute immediately without asking.
3. If the decision tree leads to "Require approval" → Ask the user explicitly before proceeding.
4. Claude never hesitates or asks for permission for commands in the "✅ Commands That Run Without Permission" lists.
5. **Note:** This rule applies to terminal commands, file creation, refactoring, and code generation. For destructive or production-affecting operations (⛔ section), Claude always requires explicit user approval via inline confirmation.

## Decision Framework

Before executing **any command**, validate:

```
1. Is it easily reversible?
   YES → Execute autonomously
   NO → Require approval

2. Does it affect production?
   YES → Require approval
   NO → Continue

3. Does it involve secrets or credentials?
   YES → Refuse; require approval
   NO → Continue

4. Is it data-destructive?
   YES → Require approval
   NO → Continue

5. Is it non-destructive & aligned with documented work?
   YES → Execute autonomously
   NO → Require approval
```

## Commands That Run Without Permission ✅

### Read-Only Operations

- `ls`, `cat`, `tail`, `wc`, `grep`, `find`, `head`, `diff`, `stat`
- `git log`, `git status`, `git diff` (inspection only, no modifications)

### Quality Gates (Readonly Checks)

- `make lint`, `make test`, `make coverage`, `make security`
- `make test-integration`, `make test-e2e`

### Code Generation & Refactoring

- Code formatting (black, isort fixes)
- Imports reorganization
- Linting fixes (flake8 violations corrected)
- Creating new files per specifications
- Editing files per requirements

### Non-Breaking Modifications

- Creating `.claude/` structure and files
- Updating documentation
- Adding new modules or features
- Modifying tests

## Commands Requiring Explicit Approval ⛔

### Destructive Operations

- `rm`, `mv`, `dd`, `chmod` on critical files
- Deleting modules or core infrastructure

### Database Operations

- Drops, truncates, destructive migrations
- Rolling back schema changes
- Purging data from production

### Deployments & Infrastructure

- Production deployments or environment changes
- Infrastructure modifications (containers, VMs, networking)
- External service integrations

### External Systems

- Modifications to external APIs or services
- Deployment to cloud platforms
- Secret management (creating, rotating credentials)

### Version Control Operations

- `git add`, `git commit`, `git push`
- Rebasing or force-pushing branches
- Merging pull requests

## Examples

| Command | Evaluation | Behavior |
|---------|-----------|----------|
| `make lint && make test` | Read-only, non-destructive | ✅ Execute immediately |
| Create new feature branch | Non-destructive, easily reversible | ✅ Execute immediately |
| Write tests for new service | Code generation, per spec | ✅ Execute immediately |
| `git commit -m "..."` | Version control operation | ⛔ Require approval |
| `make lint` fix (imports, formatting) | Code generation | ✅ Execute immediately |
| `rm app/old_module/` | Destructive | ⛔ Require approval |
| `alembic upgrade head` | Production DB operation | ⛔ Require approval (explicitly ask first) |
| Create `.claude/` structure | Non-destructive, generates files | ✅ Execute immediately |
| Review code with `git diff` | Read-only | ✅ Execute immediately |

---
