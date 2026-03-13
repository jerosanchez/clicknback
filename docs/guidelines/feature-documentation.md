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

Each spec file must contain the following sections in order:

```markdown
# XX-NN: Feature Name

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As a <role>, I want to <action> so that <benefit>._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Term** | Explanation |

---

## Constraints

### Authorization Constraints
### Input Constraints
### Behavior Constraints   ← omit if not needed

---

## BDD Acceptance Criteria

**Scenario:** ...
**Given** ... **When** ... **Then** ...

(Repeat for each significant case: happy path, main sad paths, auth failures)

---

## Use Cases

### Happy Path
1. Numbered steps.

### Sad Paths

#### Descriptive heading
1. Numbered steps.

## API Contract

See [Link text](../../../design/api-contracts/<domain>/file.md) for detailed API specifications.
```

**Rules:**

- The `## API Contract` section must link to a file in `docs/design/api-contracts/`, never embed raw JSON or endpoint details inline.
- Do not include implementation notes, code snippets, or technology references in a functional spec.
- Every spec must have at least one happy path scenario and at least one auth failure scenario in the BDD section.

See [FF-01-set-feature-flag.md](../specs/functional/feature-flags/FF-01-set-feature-flag.md) and [PU-01](../specs/functional/purchases/PU-01-create-purchase.md) as well-formed examples.

---

## 3. API Contract Format

API contracts live separately from functional specs. Each contract covers **one endpoint**.

**Location:** `docs/design/api-contracts/<domain>/<verb>-<resource>.md`

**Format:**

```markdown
# Operation Name

**Endpoint:** `METHOD /api/v1/path/{param}`
**Roles:** Admin | User | Public

---

## Request

**Path parameters** (table if any)
**Query parameters** (table if any)
**Body** (JSON block if any)

---

## Success Response

**Status:** `2XX Code`

(JSON block)

---

## Failure Responses

### 4XX Code – Description

(JSON block with `{ "error": { "code": "...", "message": "...", "details": {...} } }`)

(Repeat for each distinct failure mode)
```

**Rules:**

- Use realistic but fictional UUIDs and timestamps — no `xxx` placeholders.
- Every `4XX` response must include the corresponding internal error code string.
- Common auth failures (`401`, `403`) must always be listed.

See [set-feature-flag.md](../design/api-contracts/feature-flags/set-feature-flag.md) and [create-merchant.md](../design/api-contracts/merchants/create-merchant.md) as well-formed examples.

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
