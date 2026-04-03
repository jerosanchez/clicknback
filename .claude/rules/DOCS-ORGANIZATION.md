---
name: docs-organization
type: rule
description: How documentation is structured across docs/; folder purposes and file naming
---

# DOCS-ORGANIZATION

ClickNBack's documentation is organized into four layers, each serving a different audience and purpose.

## Documentation Layers

| Level | Location | Purpose | Audience |
|-------|----------|---------|----------|
| **Project Entry** | README.md, CONTRIBUTING.md | Overview, quickstart, contribution process | New developers, recruiters |
| **Design & Architecture** | `docs/design/` | Technical decisions, system diagrams, deployment strategies | Architects, senior engineers |
| **Functional Specs** | `docs/specs/` | What the system does, feature definitions, workflows | Product managers, QA, developers |
| **Developer Guidelines** | `docs/guidelines/` | How to implement, test, document, organize code | Developers |
| **Manual Testing** | `http/` | Interactive API request workflows | QA, developers |

## Folder Structure

```text
docs/
  design/
    adr/                           ← Architecture Decision Records
      000-technology-stack.md
      001-adopt-modular-monolith.md
      ...
    api-contracts/                 ← API endpoint contracts by domain
      auth/
      merchants/
      purchases/
      ...
    architecture-overview.md       ← System diagram and high-level architecture
    data-model.md                  ← Entity relationships, DB schema overview
    error-handling-strategy.md     ← Global error structure and codes
    security-strategy.md           ← Auth, encryption, data protection
    testing-strategy.md            ← Test pyramid rationale and organization
    deployment-plan.md             ← How to deploy, rollback, monitor
    operation-plan.md              ← How to operate in production
    adr-index.md                   ← Index of all ADRs
    api-contracts-index.md         ← Index of all API contracts
    
  specs/
    functional/                    ← Functional specs by domain
      auth/
      merchants/
      purchases/
      ...
    non-functional/
      01-data-integrity.md
      02-idempotency.md
      03-financial-precision.md
      ...
    product-overview.md            ← Product features, roadmap, positioned against competitors
    system-requirements.md         ← Non-functional requirements (performance, scalability, security)
    domain-glossary.md             ← Domain term definitions
    future-improvements.md         ← Known limitations, planned features
    workflows/                     ← User workflows (how users interact with system)
    
  guidelines/
    feature-architecture.md        ← Module anatomy, layer responsibilities
    code-organization.md           ← File splitting rules, naming conventions
    unit-testing.md                ← Unit test patterns, mocking strategies
    integration-testing.md         ← Integration test patterns, DB isolation
    end-to-end-testing.md          ← E2E test patterns, Docker Compose
    functional-specification.md    ← How to write functional specs
    api-contracts.md               ← How to write API contracts
    arch-decision-records.md       ← How to write ADRs
    markdown-docs.md               ← Markdown linting and formatting standards
    docs-organization.md           ← This document
    quality-gates.md               ← Quality, testing, linting gates
    background-jobs.md             ← How to design and test background jobs
    http-requests-file.md          ← How to write .http request files

http/
  <module>/                        ← One .http file per endpoint
    get-<resource>.http
    post-<resource>.http
    ...
```

## File Naming Conventions

### Functional Specifications

```
docs/specs/functional/<domain>/<XX-NN-short-name.md>
```

- **XX** — Two-letter domain prefix: `FF` (Feature Flags), `PU` (Purchases), `M` (Merchants), `U` (Users), `O` (Offers), `PA` (Payouts), `W` (Wallets), `AU` (Auth)
- **NN** — Two-digit sequence (01, 02, 03, ...)
- **short-name** — Kebab-case feature description

### API Contracts

```
docs/design/api-contracts/<domain>/<verb-resource>.md>
```

- **verb** — HTTP operation: `get`, `post`, `put`, `patch`, `delete`, `list`
- **resource** — Kebab-case resource name

Example: `docs/design/api-contracts/purchases/list-purchases.md`

### ADRs

```
docs/design/adr/<NNN-kebab-case-title.md>
```

- **NNN** — Zero-padded ADR number (000, 001, ..., 023)

### Guidelines

Named descriptively for their content:
- `unit-testing.md`, `functional-specification.md`, `code-organization.md`

## Update Dependencies

After creating/modifying documentation:

- Update `docs/design/adr-index.md` if you add a new ADR
- Update `docs/design/api-contracts-index.md` if you add a new API contract
- Update `docs/specs/product-overview.md` if features change
- Update `README.md` roadmap table if features ship or plans change

---
