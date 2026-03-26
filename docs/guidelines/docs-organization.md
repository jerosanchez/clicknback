# Documentation Organization

This document describes how documentation is structured across ClickNBack to make it discoverable, maintainable, and aligned with the development workflow. It covers the purpose, content, and audience for each documentation folder and how they fit together.

---

## 1. Overview: Documentation Levels

ClickNBack's documentation is organized into four layers, each serving a different purpose:

| Level | Location | Purpose | Audience |
| --- | --- | --- | --- |
| **Project Entry Points** | README.md, CONTRIBUTING.md | Project overview, quick start, contribution process | New developers, stakeholders, recruiters |
| **Design & Architecture** | `docs/design/` | Technical decisions, system architecture, deployment plans | Architects, senior engineers, decision-makers |
| **Functional Specification** | `docs/specs/` | What the system does, feature definitions, workflows, non-functional requirements | Product managers, QA, developers |
| **Developer Guidelines** | `docs/guidelines/` | How to implement, test, document, and organize code | Developers |
| **Manual Testing** | `/http` | Interactive API request workflows for manual exploration | QA, developers, demo/onboarding |
| **AI Assistance** | `.github/prompts/` | Structured prompts for AI agents to handle common tasks | AI agents, developers using AI tools |

---

## 2. Project Entry Points

### 2.1. README.md

**Location:** Project root

**Purpose:** The face of the project. Provides an executive summary, feature overview, quick-start links, and live API information.

**Content:**

- What ClickNBack is and why it exists
- Key architectural highlights and engineering rigor demonstrated
- Feature roadmap with status indicators
- Links to live API and documentation
- Instructions for trying the system without local setup
- Links to end-to-end workflows for self-guided exploration

**Audience:** Anyone discovering the project — recruiters, stakeholders, new team members, open-source contributors.

**Update Frequency:** When features ship (feature roadmap updates), when live environment changes, or quarterly.

---

### 2.2. CONTRIBUTING.md

**Location:** Project root

**Purpose:** Step-by-step setup and contribution guidelines for developers who want to work on the codebase locally.

**Content:**

- System prerequisites (Python 3.13+, Docker, etc.)
- Virtual environment setup commands
- Database initialization
- How to run tests, linters, and security checks
- Common troubleshooting (port conflicts, Docker issues, DB reset)
- References to detailed guidelines in `docs/guidelines/`

**Audience:** Developers joining the project or contributing from external sources.

**Update Frequency:** When dependencies change, setup steps change, or common issues emerge.

---

## 3. Design & Architecture: `docs/design/`

The design folder contains **Architecture Decision Records (ADRs)** and **system-wide strategy documents** that explain the "why" behind technical choices.

**Structure**:

```text
docs/design/
  adr/
    000-technology-stack-selection.md
    001-adopt-modular-monolith-approach.md
    ...
    018-feature-flag-system.md
  adr-index.md              ← Index and introduction to ADRs
  architecture-overview.md  ← High-level system architecture diagram and description
  api-contracts/            ← OpenAPI/contract specifications
  api-contracts-index.md
  data-model.md             ← Database schema, entity relationships
  deployment-plan.md        ← Production deployment strategy, secrets, rollback
  error-handling-strategy.md ← Consistent error codes, error response shapes
  operation-plan.md         ← Operational procedures, monitoring, incident response
  security-strategy.md      ← Authentication, authorization, data protection
  testing-strategy.md       ← Testing pyramid, unit vs integration vs e2e
```

### 3.1. Architecture Decision Records (ADRs)

**Location:** `docs/design/adr/`

**Purpose:** Document critical architectural and technical decisions, their context, alternatives considered, and rationale.

**Format & Structure:** See [arch-decision-records.md](./arch-decision-records.md) for the complete ADR writing guide, workflow, and template. That guide covers:

- When to write an ADR (vs. local decisions)
- Standard template and structure
- How to present options fairly
- Guidelines for balanced tradeoffs
- Team review and approval process
- How to supersede or deprecate ADRs

**Examples:**

- [ADR 001: Adopt Modular Monolith Approach](../../design/adr/001-adopt-modular-monolith-approach.md) – explains why modules are independently deployable but run in a single process
- [ADR 010: Async Database Layer](../../design/adr/010-async-database-layer.md) – why new modules use `AsyncSession` instead of synchronous SQLAlchemy
- [ADR 016: Background Job Architecture Pattern](../../design/adr/016-background-job-architecture-pattern.md) – Fan-Out Dispatcher + Per-Item Runner pattern

**Usage:** When proposing a significant architectural change, check if a relevant ADR exists first. If not, write one before implementing. This captures rationale that would otherwise be lost. Refer to [arch-decision-records.md](./arch-decision-records.md) for the full workflow.

**Audience:** Architects, senior engineers, anyone reviewing or proposing significant changes.

**Update Frequency:** As major decisions are made (typically monthly or less frequently).

---

### 3.2. Architecture Overview

**Location:** `docs/design/architecture-overview.md`

**Purpose:** System-level schematic showing modules, layers, and key interactions. Provides context for where individual features fit.

**Content:**

- Mermaid diagrams of system organization
- Description of each layer (API, services, repositories, DB)
- Module responsibilities and boundaries
- Key constraints and design principles
- Reference to relevant ADRs

**Audience:** New developers onboarding, architects reviewing the system, anyone needing to understand the big picture.

**Update Frequency:** When major modules are added or layers restructured.

---

### 3.3. API Contracts Index

**Location:** `docs/design/api-contracts/` and `docs/design/api-contracts-index.md`

**Purpose:** Precise HTTP interface specifications for every endpoint. Each contract covers one endpoint and serves as the single source of truth for request/response format, status codes, and error handling.

**Format & Writing Guide:** See [Writing API Contracts](../../guidelines/api-contracts.md) for the **authoritative guide** on how to write API contracts. That document includes:

- Mandatory section order (Title/Endpoint, Request, Success Response, Failure Responses)
- HTTP status code reference and when to use each
- Common patterns (pagination, filters, error details)
- Validation checklist before committing
- Well-formed examples to use as templates

**Usage:**

- Referenced by functional specs in the "API Contract" section.
- Used during Step 0 of `build-feature.prompt.md` to cross-check consistency with the functional spec.
- Basis for implementation: developers code exactly to these contracts.
- Basis for manual testing: `.http` files follow the contract's request/response examples.

**Audience:** Developers implementing endpoints, QA writing tests, anyone needing to know the exact HTTP interface.

**Update Frequency:** When endpoints are added or business rules change.

---

### 3.4. Strategy Documents

**Location:** `docs/design/`

**Purpose:** System-wide strategy that applies across multiple domains but is too specific for ADRs.

**Examples:**

- `error-handling-strategy.md` – Consistent error codes, error response shapes, mapping domain exceptions to HTTP status codes
- `security-strategy.md` – JWT structure, role-based access control, authentication endpoints
- `deployment-plan.md` – Docker containerization, database migrations, secrets rotation, rollback procedures
- `testing-strategy.md` – Testing pyramid, what to unit test vs integrate test, coverage targets
- `data-model.md` – Entity-relationship diagram, model descriptions, naming conventions

**Audience:** Developers implementing features in the determined strategy, architects reviewing system-wide concerns.

**Update Frequency:** When strategy changes or new system-wide concerns emerge.

---

## 4. Functional Specification: `docs/specs/`

The specs folder contains **what the system does**: functional requirements, business workflows, success criteria, and non-functional requirements.

**Structure**:

```text
docs/specs/
  functional/
    auth/
      A-01-user-login.md
    merchants/
      M-01-merchant-creation.md
      M-02-merchant-activation.md
      M-03-merchants-listing.md
    offers/
      O-01-offer-creation.md
      O-02-offer-activation.md
      ...
    purchases/
      PU-01-purchase-ingestion.md
      PU-02-purchase-confirmation.md
      ...
    users/
      U-01-user-registration.md
  non-functional/
    01-data-integrity.md
    02-idempotency.md
    03-financial-precision.md
    04-concurrency-safety.md
    ...
  workflows/
    01-admin-platform-setup.md
    02-user-discovery.md
    03-purchase-and-cashback.md
    04-wallet-and-payout.md
    end-to-end-workflows.md
    http/
      01-admin-platform-setup.http
      02-user-discovery.http
      ...
  domain-glossary.md        ← Definition of domain terms
  product-overview.md       ← High-level product description
  system-requirements.md    ← Performance, scalability, reliability requirements
  future-improvements.md    ← Planned enhancements and roadmap rationale
  ai-augmented-features.md  ← Planned AI features and use cases
```

### 4.1. Functional Specifications

**Location:** `docs/specs/functional/`

**Purpose:** Detailed specification for each feature or business capability, organized by domain.

**Format & Writing Guide:** See [Writing Functional Specifications](functional-specification.md) for the **authoritative guide** on how to write a functional specification. That document includes:

- Mandatory section order (User Story, Constraints, BDD Acceptance Criteria, Use Cases, API Contract reference)
- Detailed guidance on each section
- Common mistakes and how to avoid them
- Validation checklist before committing
- Well-formed examples to use as templates

**Quick Reference:**

Each spec includes:

- **ID & Title** (e.g., `PU-01: Purchase Ingestion`) — using the convention `XX-NN-short-name`
- **User Story** – `As a <role>, I want to <action> so that <benefit>.`
- **Constraints** – Authorization, Input, Data, and Behavior constraints (exhaustive list)
- **BDD Acceptance Criteria** – Scenarios in Given–When–Then format; must cover all major paths
- **Use Cases** – Happy Path and Sad Paths with numbered steps and error codes
- **API Contract References** – Links to `docs/design/api-contracts/<domain>/`

**Example:** [PU-01 Purchase Ingestion](../../specs/functional/purchases/PU-01-purchase-ingestion.md) describes how a purchase event is received, validated, stored idempotently, and triggers cashback calculation.

**Usage:**

- Always write or review the functional spec before implementing a feature (see `build-feature.prompt.md` Step 0).
- Always check the spec first during implementation to understand requirements.
- Always verify the implementation matches the spec during code review.
- Use specs as the requirements source for both code and test generation.

**Audience:** Developers, QA, product managers.

**Update Frequency:** When new features are planned or requirements clarify.

---

### 4.2. Non-Functional Requirements

**Location:** `docs/specs/non-functional/`

**Purpose:** System-wide quality attributes that must be met: reliability, performance, security, consistency, etc.

**Content Examples:**

- **Data Integrity** – ACID transactions, no partial state, atomicity of wallet updates
- **Idempotency** – purchases keyed by external ID prevent double-crediting on retries
- **Financial Precision** – Decimal types, rounding rules, no floating-point arithmetic
- **Concurrency Safety** – row-level locking for wallet updates, prevention of race conditions
- **Pagination** – all list endpoints support cursor-based pagination for large datasets
- **Authorization** – role-based access control, endpoint protection
- **Error Handling** – consistent error response format, meaningful error codes
- **Logging & Observability** – structured logs, audit trail, request tracing

**Audience:** Architects, developers, QA.

**Update Frequency:** When quality constraints change or new cross-cutting requirements emerge.

---

### 4.3. Workflows & End-to-End Scenarios

**Location:** `docs/specs/workflows/`

**Purpose:** Narrative-driven descriptions of complete business flows and the HTTP test files that demonstrate them.

**Content:**

- **Workflow Markdown** – Plain-language description of a multi-step business scenario from start to finish (e.g., "admin creates merchant and offer, user discovers offers, makes purchase, earns cashback, checks wallet, withdraws").
- **HTTP Test Files** – Step-by-step REST API requests that implement the workflow, runnable with VS Code REST Client.

**Workflows Included:**

1. **01-admin-platform-setup** – Admin creates a merchant and defines a cashback offer.
2. **02-user-discovery** – User registers, browses offers, sees active cashback opportunities.
3. **03-purchase-and-cashback** – User makes a purchase, cashback is calculated and confirmed.
4. **04-wallet-and-payout** – User checks wallet balance and requests a withdrawal/payout.

**Usage:**

- Start here if you're new to ClickNBack and want to understand the business domain.
- Follow the workflows step by step with REST Client to see the API in action.
- Reference for QA when validating multi-step scenarios.

**Audience:** New developers, product managers, QA, demo presentations.

**Update Frequency:** When major flows change or new workflows are introduced.

---

### 4.4. Domain Glossary

**Location:** `docs/specs/domain-glossary.md`

**Purpose:** Authoritative definitions of business domain terms to ensure consistent terminology across code and documentation.

**Content:** Definitions of terms like:

- User, Merchant, Offer, Purchase, Cashback, Wallet, Payout, Pending/Available/Paid balances
- Idempotency key, External ID, Settlement, Offer validity period, Monthly cap

**Usage:** When reading specs or code, check here for precise definitions to avoid ambiguity.

**Audience:** Everyone working on the project.

**Update Frequency:** When new domain concepts are introduced.

---

## 5. Developer Guidelines: `docs/guidelines/`

Guidelines for **how to implement, test, organize, and document code**. These are conventions and best practices enforced across the codebase.

### Structure

```text
docs/guidelines/
  code-organization.md              ← When/how to split files, module structure
  documentation-organization.md     ← (This file) How to organize docs
  arch-decision-records.md          ← How to write, review, and maintain ADRs
  feature-architecture.md           ← Layer responsibilities, how to add a new feature
  unit-testing.md                   ← Unit test structure, fixtures, mocking
  integration-testing.md            ← Integration test structure, fixtures, isolation
  end-to-end-testing.md             ← E2E test structure, Docker Compose, flows
  feature-documentation.md          ← When/how to document a new feature
  markdown-docs.md                  ← Markdown style, formatting
  http-requests-file.md             ← How to write HTTP test files
  background-jobs.md                ← Job scheduling, dispatcher/runner pattern
  project-context.md                ← Quick reference for project purpose/domain
  quality-gates.md                  ← Test coverage, linting, security checks, pre-commit hooks
```

### 5.1. Code Organization

**Location:** `docs/guidelines/code-organization.md`

**Purpose:** Practical guide for organizing code within a module as it grows: when to split files, how to structure packages, naming conventions.

**Content:**

- Default: one file per layer (models, schemas, repositories, services, etc.)
- Split thresholds: when a file becomes hard to navigate
- Splitting strategies: how to split API, services, schemas, repositories while maintaining stable imports
- Cross-module client pattern: how to depend on other modules
- Background job structure: dispatcher, runner, strategy pattern
- Core infrastructure (`app/core/`): shared cross-cutting infrastructure
- HTTP test files: smoke test organization and usage

**Audience:** Developers, code reviewers.

---

### 5.2. Architecture Decision Records

**Location:** `docs/guidelines/arch-decision-records.md`

**Purpose:** Comprehensive guide for writing, reviewing, and maintaining Architecture Decision Records (ADRs).

**Content:**

- Purpose of ADRs and why they matter
- When to write an ADR (vs. local decisions)
- Standard ADR template and structure with sections for Status, Context, Options, Decision, and Consequences
- Guidelines for strong ADRs: balanced options, explicit tradeoffs, concrete examples
- Team workflow: proposing, reviewing, and accepting ADRs
- How to supersede or deprecate ADRs when circumstances change
- How to link ADRs from code, guidelines, and prompts
- Common pitfalls to avoid
- Periodic review and maintenance of ADR corpus
- Navigation and reference

**Audience:** Architects, senior engineers, anyone proposing or reviewing significant decisions.

---

### 5.3. Feature Architecture

**Location:** `docs/guidelines/feature-architecture.md`

**Purpose:** Step-by-step guide for adding a new feature module or capability.

**Content:**

- Module anatomy: standard layer structure (models, schemas, repositories, services, policies, exceptions, errors, composition, api, clients)
- Layer responsibilities: what each layer does and doesn't do
- Dependency injection patterns: how to wire services with dependencies
- Error handling: domain exceptions vs HTTP exceptions
- Logging conventions
- Testing: unit test structure, fixtures, mocking
- Application wiring: how to register routes, inject services

**Audience:** Developers adding new features.

---

### 5.4. Testing Guidelines

**Location:** `docs/guidelines/unit-testing.md`, `docs/guidelines/integration-testing.md`, `docs/guidelines/end-to-end-testing.md`

**Purpose:** How to write tests that reflect the architecture and ensure quality.

**Content (Unit Tests):** [`unit-testing.md`](./unit-testing.md)

- Test structure and naming: `test_<module>_<layer>.py`
- Fixtures and conftest organization
- What to test: service logic, API error mapping, policies, validators
- Mocking patterns: `create_autospec`, dependency overrides
- Async test patterns: `@pytest.mark.asyncio`, `AsyncMock`
- Private function imports and type guards for optional fields

**Content (Integration Tests):** [`integration-testing.md`](./integration-testing.md)

- Integration test structure: one per endpoint
- Isolation strategy: rollback transactions, no persistence after test
- Fixtures for real database, HTTP clients
- Seeding and payload helpers
- Coverage strategy: happy path + key failure modes

**Content (End-to-End Tests):** [`end-to-end-testing.md`](./end-to-end-testing.md)

- When to write E2E tests: multi-step flows, background jobs, time transitions
- Docker Compose environment setup
- Test data creation and stateful workflows
- Async waits for background jobs

**Audience:** Developers, QA.

---

### 5.5. Other Guidelines

- **feature-documentation.md** – When and how to document new features
- **markdown-docs.md** – Markdown formatting, heading hierarchy, links
- **http-requests-file.md** – How to write HTTP test files (format, comments, edge cases)
- **background-jobs.md** – Detailed guide to the job dispatcher/runner pattern
- **project-context.md** – Quick reference for project purpose, domain, architecture
- **quality-gates.md** – Code quality checklist, pre-commit hooks, coverage targets

---

## 6. Manual Testing: `/http` Folder

**Location:** Project root `/http/` folder

**Purpose:** Interactive API request workflows for manual exploration and testing without writing automated test code.

**Structure:**

```text
/http/
  auth/
    login.http
  merchants/
    create-merchant.http
    activate-merchant.http
    list-merchants.http
  offers/
    create-offer.http
    list-offers.http
    get-active-offers.http
    get-offer-details.http
  purchases/
    ingest-purchase.http
    get-purchase-details.http
    list-all-purchases.http
  users/
    create-user.http
```

**Content Format:**

- **Setup section** – base URL, token variables, common headers
- **Happy-path request** – normal, expected-to-succeed scenario with happy path token variable
- **Sad-path requests** – edge cases, validation failures, error conditions
- **Comments** – explain what each request tests and the expected response

**Usage:**

1. Install [VS Code REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension.
2. Open an `.http` file.
3. Click the `Send Request` link above any request to execute it.
4. View the response in the side panel.

**Benefits:**

- **Quick API validation** without writing test code
- **Integration checks** before committing
- **Onboarding** – new developers follow workflows step by step
- **Demo** – run requests to showcase features
- **Documentation** – HTTP files serve as API usage examples

**Audience:** QA, developers, demo/onboarding.

**Update Frequency:** When new endpoints are added or response formats change.

---

## 7. AI Assistance: `.github/prompts/` Folder

**Location:** `.github/prompts/`

**Purpose:** Structured prompts for AI agents (like GitHub Copilot or Claude) to assist with common development tasks.

**Structure:**

```text
.github/prompts/
  add-migration.prompt.md           ← Prompt for generating database migrations
  build-feature.prompt.md           ← Prompt for implementing a new feature
  create-module.prompt.md           ← Prompt for scaffolding a new module
  review-code.prompt.md             ← Prompt for code review
  setup-for-prod.prompt.md          ← Prompt for production deployment setup
  write-unit-tests.prompt.md        ← Prompt for writing unit tests
  write-integration-tests.prompt.md ← Prompt for writing integration tests
  write-e2e-tests.prompt.md         ← Prompt for writing E2E tests
```

**Content:** Each prompt file contains:

- **Context** – project description, architecture overview
- **Task** – what the AI should do (e.g., "generate a migration that adds a field to the user table")
- **Constraints** – requirements the AI must follow (e.g., "use Alembic format", "follow the module structure in code-organization.md")
- **Output Format** – what the AI should produce (code, file structure, step-by-step instructions)
- **References** – links to relevant guidelines and documentation

**Usage:**

1. Copy the relevant prompt file.
2. Fill in the specific task details (e.g., feature name, module name).
3. Paste into your AI tool (GitHub Copilot, Claude, etc.).
4. Use the generated code as a starting point, review, and adapt as needed.

**Benefit:** Ensures AI-generated code aligns with the project's architecture and conventions.

**Audience:** Developers using AI assistants.

**Update Frequency:** When guidelines or conventions change.

---

## 8. Documentation Workflow and Best Practices

### When to Create or Update Documentation

| Event | Action |
| --- | --- |
| **New architectural decision** | Write an ADR following the template in [arch-decision-records.md](./arch-decision-records.md). Reference existing ADRs if relevant. Follow the team review workflow documented there. |
| **New feature** | Write a functional spec (e.g., `FF-01-set-feature-flag.md`) in `docs/specs/functional/`. Update the feature roadmap in README.md. |
| **New system-wide requirement** | Document in `docs/specs/non-functional/` or add an ADR if it's a decision. |
| **Change to implementation convention** | Update the relevant guideline in `docs/guidelines/`. |
| **New workflow or flow** | Add a narrative walkthrough in `docs/specs/workflows/`. Pair with HTTP test files. |
| **New API endpoint** | Add HTTP requests to `/http/` for manual testing. Link from relevant workflow documentation. |
| **Troubleshooting pattern discovered** | Add to CONTRIBUTING.md troubleshooting section. |

### Documentation Quality Checklist

- [ ] **Correct audience** – is this placed where the right people will find it?
- [ ] **Clear purpose** – does the first paragraph state why this document exists?
- [ ] **Links & references** – does it link to related docs and ADRs?
- [ ] **Examples** – are there code samples or concrete scenarios?
- [ ] **Maintainability** – would someone reviewing this code in 6 months understand it from the docs?
- [ ] **Specificity** – are implementation details concrete (not vague)?
- [ ] **Aligned with guidelines** – does it follow markdown and naming conventions?

### Keeping Documentation Current

- Review documentation during code reviews; update docs if implementation deviates.
- When fixing a bug, check if it revealed a gap in documentation; add a note.
- Quarterly: spot-check README, CONTRIBUTING, and core architecture docs for staleness.
- Setup CI checks to catch broken links in documentation (optional but recommended).

---

## 9. Documentation Navigation Map

Use this map to find what you're looking for:

**"I want to understand the project"**
→ Start with [README.md](../../README.md), then [project-context.md](./project-context.md)

**"I want to set up a development environment"**
→ [CONTRIBUTING.md](../../CONTRIBUTING.md)

**"I want to understand the code organization"**
→ [code-organization.md](./code-organization.md)

**"I want to implement a new feature"**
→ [feature-architecture.md](./feature-architecture.md), then [code-organization.md](./code-organization.md)

**"I want to understand how the system works end-to-end"**
→ [End-to-End Workflows](../../docs/specs/workflows/end-to-end-workflows.md), try the `.http` files

**"I want to understand why a design decision was made"**
→ [ADR Index](../../docs/design/adr-index.md), then read [arch-decision-records.md](./arch-decision-records.md) for context on how to read ADRs

**"I want to understand the data model"**
→ [data-model.md](../../docs/design/data-model.md)

**"I want to see all non-functional requirements"**
→ [docs/specs/non-functional/](../../docs/specs/non-functional/)

**"I want to write tests"**
→ [Unit Testing](./unit-testing.md)
→ [Integration Testing](./integration-testing.md)
→ [E2E Testing](./end-to-end-testing.md)

**"I want to deploy to production"**
→ [deployment-plan.md](../../docs/design/deployment-plan.md)

---

## 10. Maintenance and Evolution

As the project grows:

1. **New guidelines emerge** – document them in `docs/guidelines/`.
2. **New ADRs are written** – add to the index in `docs/design/adr-index.md`; update `architecture-overview.md` if it affects the big picture.
3. **Specs evolve** – update functional specs during refinement; non-functional specs when quality targets change.
4. **Docs become outdated** – during code review, flag stale documentation and update it.

Documentation is code. It should be reviewed, tested (verify links), and kept in sync with implementation just as rigorously as tests and production code.
