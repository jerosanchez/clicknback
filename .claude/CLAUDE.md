---
name: claude-instructions
type: instructions
description: Main entry point for Claude in ClickNBack
---

# ClickNBack – Claude Instructions

Start here to understand the structure and how to work with ClickNBack via Claude.

## 🚀 Quick Activation Examples

| You Say | Agent Activates | What Happens |
|---------|-----------------|-------------|
| "implement the purchase feature" | Code Agent | Loads build-feature skill + all relevant rules |
| "write tests" | Code Agent | Loads write-unit-tests skill |
| "write a functional spec" | Docs Agent | Loads write-functional-spec skill |
| "review this code" | Review Agent | Loads review-code skill |
| "@code" | Code Agent | Explicit activation (optional) |
| "@docs" | Docs Agent | Explicit activation (optional) |
| "@review" | Review Agent | Explicit activation (optional) |

---

## 🤖 Three Agents, Always In Effect

Each agent has a distinct expertise and loads relevant rules + skills automatically.

### [Code Agent](.claude/agents/code-agent.md)

Implements features, writes tests, creates modules, manages migrations, refactor code.

**Use when:** "implement", "write tests", "fix bug", "create", "write code", "refactor code"

**Skills:** build-feature, write-unit-tests, write-integration-tests, write-e2e-tests, create-module, add-migration, setup-http-request

### [Review Agent](.claude/agents/review-agent.md)

Reviews code for architecture, correctness, financial safety, and test coverage.

**Use when:** "review", "audit", "check", "security audit"

**Skills:** review-code

### [Docs Agent](.claude/agents/docs-agent.md)

Writes functional specs, API contracts, ADRs, and other documentation.

**Use when:** "write spec", "write contract", "write ADR", "document"

**Skills:** write-functional-spec, write-api-contract, write-adr

---

## 📋 Always-In-Effect Rules

These rules load automatically in every session. They define:

- **[PROJECT.md](.claude/rules/PROJECT.md)** — Product overview, entities, roles, tech stack
- **[ARCHITECTURE.md](.claude/rules/ARCHITECTURE.md)** — Module anatomy, layering, cross-module patterns
- **[CONVENTIONS.md](.claude/rules/CONVENTIONS.md)** — Code naming, error handling, async patterns
- **[QUALITY-GATES.md](.claude/rules/QUALITY-GATES.md)** — Testing, coverage, lint/security gates
- **[AUTONOMOUS-EXECUTION.md](.claude/rules/AUTONOMOUS-EXECUTION.md)** — When Claude runs commands autonomously
- **[FINANCIAL-CORRECTNESS.md](.claude/rules/FINANCIAL-CORRECTNESS.md)** — Decimal, idempotency, concurrency
- **[CODE-ORGANIZATION.md](.claude/rules/CODE-ORGANIZATION.md)** — File splitting rules, module anatomy
- **[DOCS-ORGANIZATION.md](.claude/rules/DOCS-ORGANIZATION.md)** — Folder structure, file naming
- **[MARKDOWN-STANDARDS.md](.claude/rules/MARKDOWN-STANDARDS.md)** — Markdown linting (MD025, MD001, etc.)
- **[FUNCTIONAL-SPEC-STRUCTURE.md](.claude/rules/FUNCTIONAL-SPEC-STRUCTURE.md)** — How to write specs
- **[API-CONTRACT-STRUCTURE.md](.claude/rules/API-CONTRACT-STRUCTURE.md)** — How to write contracts
- **[ADR-STRUCTURE.md](.claude/rules/ADR-STRUCTURE.md)** — How to write ADRs

---

## 🔍 Available Skills

Each skill provides:
- **index.md** — Workflow + constraints + validation checklist
- **template.md** — Code/doc templates and stubs
- **examples.md** — Real examples from ClickNBack codebase

### Coding Skills

1. **[build-feature](.claude/skills/build-feature/index.md)** — Implement a single feature/endpoint (schemas → policies → repos → services → api)
2. **[write-unit-tests](.claude/skills/write-unit-tests/index.md)** — Unit tests for services, APIs, policies
3. **[write-integration-tests](.claude/skills/write-integration-tests/index.md)** — Integration tests against real DB
4. **[write-e2e-tests](.claude/skills/write-e2e-tests/index.md)** — Full HTTP stack tests via Docker Compose
5. **[create-module](.claude/skills/create-module/index.md)** — Scaffold a new domain module
6. **[add-migration](.claude/skills/add-migration/index.md)** — Create Alembic database migrations

### Documentation Skills

7. **[write-functional-spec](.claude/skills/write-functional-spec/index.md)** — Author a feature spec (user story, constraints, BDD)
8. **[write-api-contract](.claude/skills/write-api-contract/index.md)** — Author an API contract (request/response/errors)
9. **[write-adr](.claude/skills/write-adr/index.md)** — Author an Architecture Decision Record

### Quality & Operations Skills

10. **[review-code](.claude/skills/review-code/index.md)** — Structured code review checklist
11. **[setup-for-prod](.claude/skills/setup-for-prod/index.md)** — Production deployment checklist
12. **[setup-http-request](.claude/skills/setup-http-request/index.md)** — Create manual API test files

---

## 📚 Foundational Documentation

Beyond the `.claude/` folder, reference:

- **Product & Specs**: [docs/specs/](../docs/specs/) — Functional requirements, non-functional specs, domain glossary
- **Architecture & Decisions**: [docs/design/](../docs/design/) — ADRs, data model, error strategies, security strategies

---

## ⚙️ Critical Rules That Always Apply

✅ **Modular monolith**: Strict layering (api → services → repositories → db), no cross-module direct imports

✅ **Financial correctness**: Decimal-only arithmetic, idempotency keys, SELECT FOR UPDATE on withdrawals

✅ **Testing**: Unit → Integration → E2E pyramid, 85% coverage minimum on unit tests

✅ **Quality gates**: All of `make lint && make test && make coverage && make security` must pass

✅ **Async database**: All new modules use AsyncSession; no blocking I/O in request handlers

✅ **Error handling**: Domain exceptions in services; API layer translates to HTTP errors

---

## 💡 Typical Workflows

### Workflow 1: Implement a Feature

```
You: "implement the purchase verification feature"

Claude:
  1. Detects "implement" → Code Agent activates
  2. Loads build-feature skill + ARCHITECTURE + FINANCIAL-CORRECTNESS rules
  3. Asks: Spec path? API contract?
  4. Follows: Schemas → Policies → Repos → Services → API
  5. Runs: make lint && make test && make coverage && make security
  6. Output: "Ready to push"
```

### Workflow 2: Write Tests

```
You: "write tests"

Claude:
  1. Detects "write tests" → Code Agent activates
  2. Loads write-unit-tests skill
  3. Maps BDD scenarios → Tests
  4. Writes: Policies, Services, API test suites
  5. Runs: make test && make coverage
  6. Output: "All tests pass, coverage: 87%"
```

### Workflow 3: Write Documentation

```
You: "@docs write a spec for payouts"

Claude:
  1. Detects "@docs" directive → Docs Agent activates
  2. Loads: write-functional-spec skill + MARKDOWN-STANDARDS rule
  3. Creates: User story, Constraints, BDD Acceptance Criteria, Use Cases
  4. Validates: Links to API contract, Markdown lints
  5. Output: "Spec ready at docs/specs/functional/..."
```

### Workflow 4: Code Review

```
You: "review this code for concurrency issues"

Claude:
  1. Detects "review" → Review Agent activates
  2. Loads review-code skill + FINANCIAL-CORRECTNESS rule
  3. Scans: Layering, monetary types, locks, state machines, test coverage
  4. Output: Issue list with remedies
```

---

## 🔐 Constraints & Boundaries

Claude runs commands autonomously for:
- ✅ Code generation (build features, write tests, create modules)
- ✅ Quality gates (lint, test, security)
- ✅ File creation and modification
- ✅ `.claude/` structure generation

Claude requires explicit approval for:
- ⛔ Version control (`git commit`, `git push`)
- ⛔ Destructive operations (`rm`, `mv` on critical files)
- ⛔ Production deployments or data modifications
- ⛔ Database destructive operations (drops, truncates)

---

## 🧠 Context Preservation (Saves Context Space)

**IMPORTANT DIRECTIVE:** When referencing files or rules already loaded in this session's context, **do NOT reload them**. Instead:

- Cite them as **(already in context)** or **per the [RULE_NAME] rule**
- Use short references like "as documented in PROJECT.md" or "per CONVENTIONS"
- Only load new files/rules if:
  - The session is fresh (new conversation start)
  - Explicitly asked for clarification
  - The file has been updated since it was initially loaded

**Why?** Claude's 200K token context window must prioritize active work over re-loading documentation. Initial loading of 12 rules + 3 agents = ~14,200 tokens. Avoid wasting it on redundant loads.

**Example Good Practice:**
```
Previously loaded: ARCHITECTURE rule (in context)
User: "How does cross-module access work?"
Claude: "Per ARCHITECTURE.md (already in context), cross-module access uses clients/ 
packages with DTOs, never direct imports..."
```

**Example Bad Practice:**
```
Claude: *Re-reads ARCHITECTURE.md again* "According to ARCHITECTURE.md..."
❌ Wastes 1,000 tokens on redundant load
```

---

## 📞 Quick Reference

**Project Name:** ClickNBack

**Product:** Cashback platform backend (financial correctness, idempotency, concurrency safety)

**Tech Stack:** FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, pytest, Python 3.13+

**Quality Standards:** 85% unit test coverage, zero linting/security issues, all tests passing

**Key Principle:** Comprehensive documentation before implementation; document-to-code workflow

---

## 🎯 Next Steps

Pick an agent and a task:

1. **Code Agent**: "implement the X feature" / "write tests" / "create a new module"
2. **Docs Agent**: "write a spec" / "write an API contract" / "write an ADR"
3. **Review Agent**: "review this code" / "audit the X service"

Or explore the rules and skills by clicking the links above.

---
