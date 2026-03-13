# Feature Documentation Guidelines

This document explains how to create documentation when adding a new feature to ClickNBack.
It covers the required artifacts, their locations, formats, and how they relate to each other.

---

## Overview

Every feature requires three layers of documentation:

| Layer | Purpose | Location |
| --- | --- | --- |
| **Functional spec** | What the feature does, for whom, and under what conditions | `docs/specs/functional/<domain>/` |
| **API contract** | The exact HTTP interface (endpoint, request, responses) | `docs/design/api-contracts/<domain>/` |
| **ADR** | The architectural decision behind a new system or significant change | `docs/design/adr/` |

An ADR is only required when the feature introduces a new architectural pattern, replaces an existing approach, or makes a decision with long-term consequences. Individual CRUD operations on an established module do not need an ADR.

---

## 1. One Spec Per Feature

Each functional spec covers **exactly one feature**. A feature is a single user-facing action: "Set a Feature Flag", "Delete a Feature Flag", "List Feature Flags". These are three features, not one.

**Naming convention:** `XX-NN-short-name.md`

- `XX` — two-letter domain prefix (e.g. `FF` for Feature Flags, `PU` for Purchases, `M` for Merchants)
- `NN` — two-digit sequence number within the domain (e.g. `01`, `02`)
- `short-name` — kebab-case description of the feature

**Example:** `FF-01-set-feature-flag.md`, `PU-01-create-purchase.md`

---

## 2. Functional Spec Format

For the **authoritative guide** on writing functional specifications, see [Writing Functional Specifications](functional-specification.md). That document includes the complete mandatory section order, validation checklist, common mistakes, and detailed examples.

**Quick reference:**

Each spec file must contain these sections in order:

1. **Title and Preamble** – `# XX-NN: Feature Name` with "IMPORTANT: This is a living document..."
2. **User Story** – `As a <role>, I want to <action> so that <benefit>.`
3. **Domain Concepts** (optional) – Table of unfamiliar terms
4. **Constraints** – Authorization, Input, Data, and Behavior constraints (be exhaustive)
5. **BDD Acceptance Criteria** – Scenarios in Given–When–Then format; must cover: happy path, auth failures, validation failures, business-rule failures
6. **Use Cases** – Numbered step-by-step flows for happy and sad paths (one per failure mode)
7. **API Contract** – Link(s) to `docs/design/api-contracts/<domain>/`

**Essential rules:**

- One feature per spec file (e.g., "Set Feature Flag", not "Feature Flags").
- Naming: `XX-NN-short-name.md` (two-letter domain prefix, two-digit sequence number, kebab-case description).
- Never embed JSON or HTTP details — put those in the API Contract.
- Constraints must be exhaustive; every validation rule and authorization check goes here.
- BDD scenarios must be concrete with examples, not abstract placeholders.
- Use cases must trace complete flows and include error codes.

See well-formed examples for reference:

- [A-01-user-login.md](../specs/functional/auth/A-01-user-login.md)
- [FF-01-set-feature-flag.md](../specs/functional/feature-flags/FF-01-set-feature-flag.md)
- [PU-01-purchase-ingestion.md](../specs/functional/purchases/PU-01-purchase-ingestion.md)

---

## 3. API Contract Format

For the **authoritative guide** on writing API contracts, see [Writing API Contracts](api-contracts.md). That document includes the complete mandatory section order, validation checklist, common mistakes, HTTP status code reference, and detailed examples.

**Quick reference:**

Each contract file describes **one endpoint** and must contain:

1. **Title and Endpoint Declaration** – Operation name, HTTP method + path, allowed roles
2. **Request** – Tables for path params, query params, and JSON body with field descriptions
3. **Success Response** – HTTP status code and realistic JSON response example
4. **Failure Responses** – All error modes with error codes, status codes, and context

**Naming:** `<verb>-<resource>.md` (e.g., `set-feature-flag.md`, `list-merchants.md`)

**Location:** `docs/design/api-contracts/<domain>/`

**Essential rules:**

- One endpoint per contract (e.g., PUT `/feature-flags/{key}`, not multiple endpoints).
- Every failure scenario from the functional spec must have a response in the contract.
- Error codes must be specific (e.g., `MERCHANT_NOT_FOUND`, not generic `NOT_FOUND`).
- Use realistic but fictional data: valid UUIDs (not `xxx`), real timestamps (ISO 8601), actual enum values.
- Always include mandatory auth failures (401, 403 if applicable) and 500 Internal Server Error.
- Error response shape: `{ "error": { "code": "...", "message": "...", "details": {...} } }`.

See well-formed examples for reference:

- [set-feature-flag.md](../design/api-contracts/feature-flags/set-feature-flag.md)
- [create-merchant.md](../design/api-contracts/merchants/create-merchant.md)
- [list-feature-flags.md](../design/api-contracts/feature-flags/list-feature-flags.md)

---

## 4. Updating the Index Files

After creating new documentation files, update the relevant index files:

| Index file | What to update |
| --- | --- |
| `docs/design/api-contracts-index.md` | Add a section for the new domain (or a link in the existing section) |
| `docs/specs/functional/` | No index required; directory listing is sufficient |
| `README.md` roadmap table | Add one row per feature with status (`⚪ backlog`, `⚫ planned`, `🟡 in progress`, `🟢 done`) |

---

## 5. When to Write an ADR

Write an ADR when a feature:

- Introduces a new infrastructure pattern (e.g. a queue, a cache, a flag system)
- Replaces or deprecates an existing approach
- Makes a decision that constrains future work
- Involves a trade-off that future developers must understand

**Naming convention:** `NNN-short-title.md` (sequential number, see `docs/design/adr-index.md` for the next available number)

After writing the ADR, add it to `docs/design/adr-index.md`.

See [ADR-018](../design/adr/018-feature-flag-system.md) as a well-formed example.

---

## 6. Review and Update Core Docs

After documenting a new feature, always review and update the following files to ensure the system documentation remains consistent and comprehensive:

- `docs/specs/product-overview.md` — Update the product overview to reflect new features, flows, or architectural changes.
- `docs/specs/system-requirements.md` — Add or revise functional/non-functional requirements as needed.
- `docs/specs/future-improvements.md` — Identify new opportunities or technical improvements related to the feature.
- `docs/specs/domain-glossary.md` — Add new domain terms or update definitions impacted by the feature.

## 7. Quick Checklist

When documenting a new feature, verify:

- [ ] One spec file per feature, not one per domain area
- [ ] Spec file follows the mandatory section order
- [ ] No raw endpoint or JSON schema in the spec (link to API contract instead)
- [ ] API contract file created in `docs/design/api-contracts/<domain>/`
- [ ] `docs/design/api-contracts-index.md` updated
- [ ] `README.md` roadmap table updated with one row per feature
- [ ] ADR written if the feature introduces an architectural decision
- [ ] `docs/design/adr-index.md` updated if an ADR was written
- [ ] `docs/specs/product-overview.md` reviewed/updated
- [ ] `docs/specs/system-requirements.md` reviewed/updated
- [ ] `docs/specs/future-improvements.md` reviewed/updated
- [ ] `docs/specs/domain-glossary.md` reviewed/updated
