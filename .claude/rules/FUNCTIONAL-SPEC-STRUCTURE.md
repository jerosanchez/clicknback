---
name: functional-spec-structure
type: rule
description: Structure and mandatory sections for functional specification documents
---

# FUNCTIONAL-SPEC-STRUCTURE

## Overview

A functional specification is the **single source of truth** for a feature. It describes what the feature does, when it can be used, why business rules matter, and how users interact with it. Functional specs are implementation-agnostic — no code, databases, or API details.

**Note on Front Matter:** Functional specs are regular Markdown files (`.md`) stored in `docs/specs/`. Do not add YAML front matter. Per [MARKDOWN-STANDARDS.md](./MARKDOWN-STANDARDS.md), only use official front matter keys (name, type, description) for files in `.claude/` folder. Spec files themselves should not have front matter.

## One Spec Per Feature

Write one spec per user-facing action, not per domain area.

**Correct:**
- "Set a Feature Flag" ✅ (one feature)
- "Delete a Feature Flag" ✅ (one feature)

**Incorrect:**
- "Feature Flag Management" ❌ (multiple features)

## Naming Convention

```
docs/specs/functional/<domain>/<XX-NN-short-name.md>
```

- **XX** — Two-letter domain prefix (FF, PU, M, U, O, PA, W, AU)
- **NN** — Two-digit sequence (01, 02, 03, ...)
- **short-name** — Kebab-case description

Example: `docs/specs/functional/purchases/PU-01-purchase-ingestion.md`

## Mandatory Sections (In Order)

### 1. Title and Preamble

```markdown
# XX-NN: Feature Name

IMPORTANT: This is a living document. Specifications are subject to change.
```

### 2. User Story

```markdown
## User Story

_As a <role>, I want to <action> so that <benefit>._
```

Single sentence in given–want–benefit format. Examples:
- "As a registered user, I want to submit a purchase so that I can earn cashback."
- "As an admin, I want to approve payouts so that users receive their rewards."

### 3. Domain Concepts (Optional)

```markdown
## Domain Concepts

| Term | Description |
| --- | --- |
| **Flag Key** | Unique string identifier, e.g., `purchase_confirmation_job` |
| **Scope Type** | `global`, `merchant`, or `user` |
```

Only include if the feature introduces unfamiliar domain terminology.

### 4. Constraints

```markdown
## Constraints

- Authorization: Admin role required ✅; user cannot see other users' data
- Input validation: Amount must be > 0 and ≤ 10,000 EUR
- Data dependencies: Purchase cannot reference non-existent merchant
- Idempotency: Duplicate requests (same external_id) are safely rejected
- Rate limiting: Max 100 requests per minute per user
```

List **every** rule: every authorization check, input rule, and data dependency.

### 5. BDD Acceptance Criteria

```markdown
## Acceptance Criteria

### Happy Path (Scenario 1: User submits valid purchase)
Given: User is registered and active
When: POST /purchases with valid merchant_id, amount, external_id
Then: Purchase is created (status=pending), cashback transaction queued, wallet updated, HTTP 201

### Failure Mode 1: Missing required field
Given: User is registered
When: POST /purchases without required merchant_id
Then: HTTP 422 with error code VALIDATION_ERROR

### Failure Mode 2: Merchant not found
Given: User is registered
When: POST /purchases with non-existent merchant_id
Then: HTTP 404 with error code MERCHANT_NOT_FOUND

### Failure Mode 3: Duplicate external_id
Given: Previous purchase with external_id="ABC-123"
When: POST /purchases with same external_id="ABC-123"
Then: HTTP 409 CONFLICT with error code DUPLICATE_PURCHASE
```

Cover: happy path, auth failures, validation failures, business rule failures.

### 6. Use Cases

```markdown
## Use Cases

### Use Case 1: Purchase Ingestion (Happy Path)
1. External system submits purchase: merchant_id, amount, currency, external_id
2. System validates: merchant exists, amount > 0, currency == EUR
3. System creates Purchase with status=pending
4. System determines applicable offer
5. System queues CashbackTransaction (status=pending)
6. System updates wallet.pending += cashback_amount
7. System returns Purchase with ID and status
8. Background job confirms purchase after X seconds
9. Wallet transitions: pending → available
```

Explain the happy path flow, then key alternate paths (failures).

### 7. API Contract Link

```markdown
## API Contract

[create-purchase (API contract)](../../docs/design/api-contracts/purchases/create-purchase.md)
```

Link to the corresponding API contract document.

## Template

```markdown
# XX-NN: Short Feature Name

IMPORTANT: This is a living document. Specifications are subject to change.

## User Story

_As a <role>, I want to <action> so that <benefit>._

## Domain Concepts

(Optional; include only if needed)

| Term | Description |
| --- | --- |
| **Term Name** | Definition |

## Constraints

- Authorization: ...
- Input validation: ...
- Data dependencies: ...
- Idempotency: ...

## Acceptance Criteria

### Happy Path Scenario 1: ...
Given: ...
When: ...
Then: ...

### Failure Mode 1: ...
Given: ...
When: ...
Then: ...

... (more scenarios)

## Use Cases

### Use Case 1: Main Flow ...
1. ...
2. ...

### Use Case 2: Alternate Flow ...
1. ...

## API Contract

[Link to API contract]
```

---
