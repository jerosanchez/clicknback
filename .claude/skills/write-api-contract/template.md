---
# template.md for write-api-contract
---

# API Contract Template

```markdown
# Operation Name

**Endpoint:** `METHOD /api/v1/path/{param}`  
**Roles:** User, Admin  
**Related Spec:** [Spec Link](../../docs/specs/functional/<domain>/<spec>.md)

## Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| - | - | - | (none) |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| - | - | - | (none) |

**Body (application/json):**

\`\`\`json
{
  "field": "value"
}
\`\`\`

**Field Descriptions:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `field` | string | ✅ | max 255 | Description |

**Authentication:** Bearer token (JWT)

**Example:**

\`\`\`bash
curl -X POST http://localhost:8001/api/v1/endpoint \\
  -H "Authorization: Bearer <token>" \\
  -H "Content-Type: application/json" \\
  -d '{"field": "value"}'
\`\`\`

## Success Response

**Status Code:** \`201 Created\`

**Response Body (application/json):**

\`\`\`json
{
  "id": "uuid",
  "field": "value"
}
\`\`\`

## Failure Responses

### 401 Unauthorized
\`\`\`json
{
  "error": {"code": "UNAUTHORIZED", "message": "...", "details": {}}
}
\`\`\`

### 422 Unprocessable Entity
\`\`\`json
{
  "error": {"code": "INVALID_REQUEST", "message": "...", "details": {}}
}
\`\`\`

### 404 Not Found
\`\`\`json
{
  "error": {"code": "NOT_FOUND", "message": "...", "details": {}}
}
\`\`\`
```
