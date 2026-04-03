# ClickNBack Development – Claude AI Integration Guide

Welcome! This folder contains AI instructions and workflows for ClickNBack. It enables seamless work in **VS Code**, **Claude Code**, or via **Claude.ai** — all synced to the same instruction set.

---

## 🚀 Quick Start (5 Minute Orientation)

### For Your First Task

1. **Open CLAUDE.md** — It loads automatically at session start; defines agents & rules
2. **Pick your task type:**
   - "implement a feature" → **Code Agent** activates
   - "write tests" → **Code Agent** loads testing skills
   - "write a spec" → **Docs Agent** activates
   - "review code" → **Review Agent** activates
3. **Tell Claude what you need** (just ask naturally)
4. **Claude autonomously:**
   - Loads relevant rules & skills
   - Follows architecture patterns
   - Runs quality gates (lint, test, coverage)
   - Outputs production-ready code

### What Gets Auto-Loaded

Every session automatically loads:
- **CLAUDE.md** (~700 tokens): Entry point + navigation
- **12 Rules** (~12,000 tokens): ClickNBack standards & patterns
- **Agent definitions**: code, review, docs agents with auto-activation keywords

**Total baseline: ~14,200 tokens** (only 7% of Claude's 200K context window)

This leaves **~185K tokens for your actual work** — plenty of room.

---

## 📁 Folder Structure

```
.claude/
├── README.md              ← You are here
├── CLAUDE.md              ← Auto-loaded entry point (start here when confused)
├── rules/                 ← 12 always-loaded foundations
│   ├── PROJECT.md         ← Product, entities, roles, tech stack
│   ├── ARCHITECTURE.md    ← Modular monolith, layering, clients
│   ├── CONVENTIONS.md     ← Naming, error codes, ORM patterns
│   ├── QUALITY-GATES.md   ← Testing pyramid, coverage, lint/security
│   ├── AUTONOMOUS-EXECUTION.md ← When Claude auto-runs commands
│   ├── FINANCIAL-CORRECTNESS.md ← Decimal, idempotency, locks
│   ├── CODE-ORGANIZATION.md ← File splitting, _helpers pattern
│   ├── DOCS-ORGANIZATION.md ← Docs folder structure, file naming
│   ├── MARKDOWN-STANDARDS.md ← Linting rules (MD025, MD001, etc.)
│   ├── FUNCTIONAL-SPEC-STRUCTURE.md ← How to write specs
│   ├── API-CONTRACT-STRUCTURE.md ← How to write API contracts
│   └── ADR-STRUCTURE.md ← How to write architecture decisions
├── agents/                ← 3 agent definitions (implicit & explicit activation)
│   ├── code-agent.md      ← Implements features, writes tests, creates modules
│   ├── review-agent.md    ← Reviews code for quality & safety
│   └── docs-agent.md      ← Writes specs, contracts, ADRs
└── skills/                ← 12 specialized workflows (each with 3 files)
    ├── build-feature/     ← Implement endpoint (schema → api)
    ├── write-unit-tests/  ← Unit tests (AAA, mocking, fixtures)
    ├── write-integration-tests/ ← Real DB tests
    ├── write-e2e-tests/   ← Full HTTP flows via Docker Compose
    ├── create-module/     ← Scaffold domain modules
    ├── add-migration/     ← Alembic workflow
    ├── write-functional-spec/ ← Feature requirements
    ├── write-api-contract/ ← API endpoint docs
    ├── write-adr/         ← Architectural decisions
    ├── review-code/       ← Code audit checklist
    ├── setup-for-prod/    ← Production deployment
    └── setup-http-request/ ← Manual API test files
```

---

## 🤖 How the Agent System Works

### Automatic Agent Activation (Implicit)

When you write a request, Claude detects keywords and auto-activates the right agent:

| Your Request | Detected Keyword | Agent Activated | Skills Loaded |
|--------------|------------------|-----------------|--------------|
| "implement the wallet feature" | `implement` | code-agent | build-feature |
| "write tests for purchases" | `write tests` | code-agent | write-unit-tests |
| "write a spec for payouts" | `write spec` | docs-agent | write-functional-spec |
| "review the concurrency logic" | `review` | review-agent | review-code |
| "set up for production" | N/A | Ask at start | setup-for-prod |

**Keywords for Code Agent:**
- implement, create, build, add, refactor, fix, write code, write tests

**Keywords for Docs Agent:**
- write spec, write contract, write ADR, document, design, architecture

**Keywords for Review Agent:**
- review, audit, check, security audit, analyze

### Explicit Agent Activation (Directive)

You can also explicitly choose an agent using a prefix directive:

```
@code implement the purchase verification feature

@docs write a spec for payout reversals

@review check the wallet withdrawal logic for concurrency issues
```

**When to use explicit:**
- Ambiguous requests (could trigger multiple agents)
- Want to be absolutely sure which agent runs
- Testing/debugging the system

---

## 📋 What Each Agent Does

### Code Agent

**Purpose:** Implements features, writes tests, creates modules, manages migrations

**Default Actions:**
- Follows strict layering: api → services → policies → repositories → db
- Uses `async`/`await` throughout; no blocking I/O
- Financial correctness: `Decimal` only, idempotency, concurrency safety
- Unit tests with mocking; integration tests with real DB
- Autonomously runs quality gates (`make lint && make test && make coverage && make security`)

**Example Workflow:**
```
You: "implement user registration"
Code Agent:
  1. Asks for spec path & API contract location
  2. Creates schemas (input validation)
  3. Creates policies (business rules)
  4. Creates repositories (DB access)
  5. Creates services (orchestration)
  6. Creates API endpoints (HTTP)
  7. Writes unit tests (all layers)
  8. Runs quality gates
  Output: "Ready to push"
```

### Review Agent

**Purpose:** Audits code for architecture, correctness, financial safety, test coverage

**Default Checks:**
- ✅ Layering: api ≠ services ≠ policies ≠ repositories
- ✅ Financial: All amounts are `Decimal`, not `float`
- ✅ Async: No blocking I/O in request handlers
- ✅ Concurrency: Wallet writes use `SELECT FOR UPDATE`
- ✅ Testing: Unit tests mocked; integration tests real DB; E2E flows complete
- ✅ Idempotency: External transactions have unique keys

**Example Workflow:**
```
You: "review the payout approval logic"
Review Agent:
  1. Reads your code
  2. Checks all conventions (naming, structure)
  3. Verifies financial safety (locks, decimal types)
  4. Checks test coverage
  Output: "✅ Ready to merge" or "⛔ Issues found: ..."
```

### Docs Agent

**Purpose:** Writes functional specs, API contracts, architecture decision records

**Default Outputs:**
- **Functional Spec:** User story, constraints, BDD scenarios, use cases
- **API Contract:** Request/response schemas, all error codes, examples
- **ADR:** Context, options considered, decision rationale, consequences

**Example Workflow:**
```
You: "@docs write a spec for bonus point expiration"
Docs Agent:
  1. Creates user story
  2. Lists constraints (date math, financial impact)
  3. Writes BDD scenarios (happy path, failures)
  4. Links to API contract
  Output: "Spec ready at docs/specs/functional/..."
```

---

## 💡 Example Workflows

### Workflow 1: Implement a Feature (Complete Walkthrough)

```
You: "implement the purchase confirmation job; should confirm pending
purchases after 5 minutes and create cashback transactions"

Claude (code-agent):
  [Loads build-feature skill + ARCHITECTURE + CONVENTIONS rules]

Claude: "Let me implement this. First, I need:
  1. Spec path (should I read/create one?)
  2. API contract path
  3. Do you want integration tests?"

You: "Spec already exists at docs/specs/functional/purchases/PU-03-purchase-confirmation.md
      API contract at docs/design/api-contracts/purchases/confirm-purchase.md"

Claude:
  ✅ Reads spec + contract
  ✅ Creates schemas (PurchaseConfirmIn, PurchaseConfirmOut)
  ✅ Creates policy: enforce_confirmed_state(purchase) → validates state
  ✅ Creates repository: Repository.confirm_purchase(db, id)
  ✅ Creates service: Service.confirm_purchase(uow, purchase_id)
  ✅ Creates API endpoint: POST /purchases/{id}/confirm
  ✅ Creates unit tests (mocked DB, policy rules, service logic)
  ✅ Creates integration tests (real DB, transaction rollback)
  ✅ Runs: make lint && make test && make coverage && make security

Output:
  "Feature ready. Files created:
   ✅ app/purchases/schemas.py (3 new classes)
   ✅ app/purchases/policies.py (1 new function)
   ✅ app/purchases/repositories.py (1 new method)
   ✅ app/purchases/services.py (1 new method)
   ✅ app/purchases/api.py (1 new route)
   ✅ tests/unit/purchases/ (4 new test files)
   ✅ tests/integration/purchases/ (1 new test file)
   
   All tests pass. Coverage: 87%. Ready to push."
```

### Workflow 2: Write Tests for Existing Code

```
You: "write comprehensive tests for the wallet service"

Claude (code-agent):
  [Loads write-unit-tests skill]

Claude: "I'll write unit and integration tests. 
         Let me map the service methods to BDD scenarios..."

Output:
  "Tests written:
   ✅ tests/unit/wallets/test_service_get_balance.py (5 scenarios)
   ✅ tests/unit/wallets/test_service_withdraw.py (8 scenarios)
   ✅ tests/integration/wallets/test_withdrawal_flow.py (3 flows)
   
   Coverage: 91%
   All tests pass.
   Ready for review."
```

### Workflow 3: Code Review

```
You: "review the merchant creation endpoint for security and financial correctness"

Claude (review-agent):
  [Loads review-code skill + FINANCIAL-CORRECTNESS rule]

Claude:
  ✅ Reads code
  ✅ Checks layering (no business logic in API)
  ✅ Checks authorization (admin role required?)
  ✅ Checks validation (merchant data constraints)
  ✅ Checks financial (no float usage)
  ✅ Checks tests (proper mocking, edge cases)

Output:
  "✅ APPROVED
   
   Strengths:
   • Clean separation of concerns
   • Proper async/await usage
   • Good test coverage (88%)
   
   Minor suggestions:
   • Line 45: Add validation for merchant name length
   • Line 67: Consider adding rate limiting
   
   Ready to merge."
```

### Workflow 4: Write Documentation

```
You: "@docs write an ADR for event-driven audit logging"

Claude (docs-agent):
  [Loads write-adr skill + ADR-STRUCTURE rule]

Output:
  "ADR written: docs/design/adr/023-event-driven-audit-logging.md
   
   Sections included:
   ✅ Title + Status (Proposed)
   ✅ Context (why audit trails matter)
   ✅ Options (3 alternatives considered)
   ✅ Decision (chosen approach)
   ✅ Consequences (positive & negative)
   
   Ready for team review."
```

---

## 🔐 Autonomous Execution: What Claude Does Without Asking

Claude **automatically executes** (no approval needed):
- ✅ Read-only: `ls`, `find`, `grep`, `git log`, `git status`
- ✅ Quality gates: `make lint`, `make test`, `make coverage`, `make security`
- ✅ Code generation: Create files, edit code per spec
- ✅ Formatting: Black, isort, flake8 fixes
- ✅ Non-destructive: Creating `.claude/` files, updating docs

Claude **requires explicit approval** for:
- ⛔ Destructive: `rm`, `mv` on critical files
- ⛔ Git operations: `git add`, `git commit`, `git push`
- ⛔ Database: Destructive migrations, drops, truncates
- ⛔ Production: Deployments, infrastructure changes
- ⛔ External: API modifications, secret management

---

## 🧠 Context Preservation (Saves Tokens)

**Important:** When referencing rules/files already loaded in this session:

**Instead of:**
```
Claude: "Let me re-read ARCHITECTURE.md to confirm..."
❌ Wastes 1,000 tokens reloading the file
```

**Do this:**
```
Claude: "Per ARCHITECTURE.md (already in context), the modular monolith uses..."
✅ Saves tokens by referencing cached knowledge
```

**Rule of thumb:**
- If a rule was loaded at session start (in CLAUDE.md), it's in context
- Cite it by name: "per PROJECT rule", "as per CONVENTIONS (already loaded)"
- Only reload if you explicitly ask: "Can you re-read X for clarity?"

---

## ❓ Frequently Asked Questions

### "How do I activate a specific agent?"

**Implicit (natural language):**
```
"implement X" → code-agent
"write tests" → code-agent
"write spec" → docs-agent
"review code" → review-agent
```

**Explicit (directive):**
```
@code implement X
@docs write spec for X
@review check X
```

### "What's the difference between unit and integration tests?"

**Unit tests** (in context)
- All dependencies mocked
- Run in <100ms
- Test one layer in isolation

**Integration tests** (in context)
- Real PostgreSQL database
- Rolls back after each test
- Test layers interacting

See [QUALITY-GATES.md](rules/QUALITY-GATES.md) for full details.

### "Why doesn't Claude ask me for approval for most changes?"

Per [AUTONOMOUS-EXECUTION.md](rules/AUTONOMOUS-EXECUTION.md), Claude follows a decision tree:
1. Is it easily reversible? → Execute autonomously
2. Does it affect production? → Require approval
3. (etc.)

Changes to code/tests/docs are reversible (via git), so Claude executes them. Destructive operations (deletes, production deployments) require approval.

### "What's auto-loaded every session?"

From [CLAUDE.md](CLAUDE.md):
- ✅ CLAUDE.md itself (~700 tokens)
- ✅ All 12 rules (~12,000 tokens)
- ✅ Agent metadata

Total: ~14,200 tokens. This leaves ~185K for your actual work.

### "I'm confused about which agent to use."

Start with [CLAUDE.md](CLAUDE.md) — it has a quick reference table. Or just describe what you want naturally; Claude detects keywords and auto-activates.

---

## 📚 Key Documentation

Inside `.claude/`:
- **[CLAUDE.md](CLAUDE.md)** — Auto-loaded entry point; agent definitions
- **[rules/](rules/)** — 12 foundational patterns (always-loaded)
- **[agents/](agents/)** — 3 agent definitions with activation keywords
- **[skills/](skills/)** — 12 specialized workflows with templates & examples

Outside `.claude/` (referenced from skills):
- **[docs/specs/](../docs/specs/)** — Functional requirements
- **[docs/design/](../docs/design/)** — Architecture, ADRs, API contracts

---

## 🎯 Next Steps

1. **Read [CLAUDE.md](CLAUDE.md)** — 2 min overview
2. **Pick a task** ("implement X", "write tests", "write spec")
3. **Tell Claude what you need**
4. **Claude handles the rest** (agent activation, skill loading, quality gates)

**Your first feature implementation should take ~30 minutes** (design + code + tests + validation).

---

**Questions?** Check [CLAUDE.md](CLAUDE.md#-typical-workflows) for workflow examples, or ask Claude directly — it loads this entire system into context automatically.

**Welcome to ClickNBack!** 🚀
