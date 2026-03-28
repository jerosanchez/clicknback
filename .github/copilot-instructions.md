# AI Behavior & Instructions for ClickNBack

## Autonomous Command Execution

The AI agent executing tasks in this repository is configured to run non-destructive commands autonomously without asking for permission.

### Commands That Run Without Permission ✅

- **Read-only commands**: `ls`, `cat`, `tail`, `wc`, `grep`, `find`, `head`, `diff`, `stat`
- **Quality gates**: `make lint`, `make test`, `make coverage`, `make security`, `make test-integration`, `make-test-e2e`
- **Code generation & refactoring**: Code formatting, imports reorganization, linting fixes
- **Non-breaking file modifications**: Creating new files per specifications, editing files per requirements
- **Git inspection**: `git log`, `git status`, `git diff` (read-only operations)

### Commands Requiring Explicit Approval ⛔

- **Destructive operations**: `rm`, `mv`, `dd`, `chmod` on critical files
- **Database operations**: Drops, truncates, destructive migrations
- **Deployments**: Production deployments or infrastructure changes
- **External services**: Modifications to external systems or APIs
- **Version control operations**: Staging, committing, or pushing changes

---

## Decision Framework

Before executing any command, the AI validates:

1. **Is it easily reversible?** → If yes, execute autonomously
2. **Does it affect production?** → If yes, require approval
3. **Does it involve secrets?** → If yes, refuse and require approval
4. **Is it data-destructive?** → If yes, require approval
5. **Is it non-destructive & aligned with documented work?** → Execute autonomously

---

## ClickNBack Project Context

This repository contains **ClickNBack**, a production-grade cashback platform backend demonstrating financial correctness, idempotency, and concurrency safety.

### Key Constraints

- `.github/` instructions files are the source of truth for AI behavior
- `AGENTS.md` at root applies project-wide
- Always check `.github/prompts/` for task templates before implementing

---

## Behavior Summary

**This file ensures that all AI agents (GitHub Copilot, Claude Haiku, etc.) running in this repository automatically execute quality gates, code generation tasks, and non-destructive operations without blocking on permission requests.**

For details on architecture, modules, and development practices, see the root-level `AGENTS.md` file.
