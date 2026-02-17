# Request a withdrawal from the user's available wallet balance

**Endpoint:** `POST /users/wallet/withdraw`

**Roles:** Authenticated User

## Request

```json
{
  "amount": 50.00,
  "method": "bank_transfer",
  "details": {
    "iban": "ES9121000418450200051332",
    "account_holder": "Alice Example"
  }
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "c1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "requested",
  "amount": 50.00,
  "requested_at": "2026-02-13T12:30:00Z"
}
```

## Failure Responses

- **400 Bad Request** – invalid request payload

  ```json
  { "error": "Invalid amount or missing bank details" }
  ```

- **403 Forbidden** – withdrawal policy not met (e.g., minimum amount, frequency cap)

  ```json
  { "error": "Withdrawal policy not satisfied" }
  ```

- **409 Conflict** – insufficient available balance

  ```json
  { "error": "Available balance (25.50) is less than requested amount (50.00)" }
  ```

- **401 Unauthorized** – user not authenticated

  ```json
  { "error": "Unauthorized" }
  ```
