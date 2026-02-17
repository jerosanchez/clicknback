# Request payout

**Endpoint:** `POST /users/payouts`

**Roles:** Authenticated

## Request

```json
{
  "amount": 20.00,
  "method": "bank_transfer",
  "details": {
    "iban": "ES9121000418450200051332"
  }
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "requested",
  "amount": 20.00
}
```

## Failure Responses

- **400 Bad Request** – insufficient funds
- **403 Forbidden** – policy violation
