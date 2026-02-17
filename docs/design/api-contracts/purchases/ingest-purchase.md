# Ingest purchase

**Endpoint:** `POST /purchases`

**Roles:** External / System

**Note:** This endpoint is idempotent.

## Request

```json
{
  "external_id": "txn_001",
  "user_id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a",
  "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "amount": 100.50,
  "currency": "EUR"
}
```

## Success Response

**Status:** 201 Created or 200 OK if duplicate

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "pending",
  "cashback_amount": 0
}
```

## Failure Responses

- **400 Bad Request** – missing fields
- **409 Conflict** – duplicate external_id (returns existing purchase)
