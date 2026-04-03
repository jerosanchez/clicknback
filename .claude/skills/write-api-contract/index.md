---
name: write-api-contract
type: skill
description: Write an API contract document
---

# Skill: Write API Contract

Write an API contract document — the specification of exactly one HTTP endpoint.

## Before Starting

1. **Read the functional spec** — Contract must satisfy all acceptance criteria
2. **Choose naming**: `docs/design/api-contracts/<domain>/<verb-resource>.md`
3. **Read API-CONTRACT-STRUCTURE rule** — Covers all mandatory sections

## Workflow

### Section 1: Title & Endpoint

```markdown
# Create Purchase

**Endpoint:** `POST /api/v1/purchases`  
**Roles:** User, Admin  
**Related Spec:** [PU-01 Purchase Ingestion](../../specs/functional/purchases/PU-01-purchase-ingestion.md)
```

### Section 2: Request

- Path parameters (if any)
- Query parameters (if any)
- Request body schema
- Field descriptions and validation rules
- Authentication method
- Example curl request

### Section 3: Success Response

- HTTP status code (201 for POST, 200 for GET/PUT, 204 for DELETE)
- Response body schema
- Field descriptions

### Section 4: Failure Responses

One block per error scenario. Include:
- HTTP status code (400, 401, 403, 404, 409, 422, 500)
- Error code (specific, e.g., `MERCHANT_NOT_FOUND`)
- Error message and details

---
