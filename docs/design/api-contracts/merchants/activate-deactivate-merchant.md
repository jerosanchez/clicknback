# Activate/deactivate merchant

**Endpoint:** `PATCH /merchants/{id}/status`

**Roles:** Admin

## Request

```json
{
  "status": "inactive"
}
```

## Success Response

**Status:** 200 OK

```json
{
  "id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "status": "inactive"
}
```

## Failure Responses

- **404 Not Found** – merchant not found
- **400 Bad Request** – invalid status
- **403 Forbidden** – non-admin
