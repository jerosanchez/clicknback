---
name: autonomous-execution
type: rule
description: Decision framework for when Claude runs commands autonomously vs. requires approval
---

# AUTONOMOUS-EXECUTION

**🤖 DIRECTIVE: Claude MUST use this rule to make autonomous execution decisions. Apply the decision framework below to every command without asking for permission unless explicitly listed in "Commands Requiring Explicit Approval".**

Claude in this project is configured to autonomously execute non-destructive commands and require explicit approval for destructive or high-risk operations.

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
