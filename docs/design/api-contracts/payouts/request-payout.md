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

### 400 Bad Request – Validation Error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for request body.",
    "details": {
      "violations": [
        {
          "field": "amount",
          "reason": "Amount must be positive and a valid decimal."
        },
        {
          "field": "method",
          "reason": "Payment method must be one of: bank_transfer, card."
        },
        {
          "field": "details",
          "reason": "Bank transfer requires IBAN. Card transfer requires card details."
        }
      ]
    }
  }
}
```

### 401 Unauthorized – Missing Authentication

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication token is missing or invalid.",
    "details": {
      "issue": "Token expired or malformed",
      "action": "Include a valid Bearer token in the Authorization header."
    }
  }
}
```

### 409 Conflict – Insufficient Available Balance

```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Insufficient available balance. Requested: 50.00, Available: 25.50.",
    "details": {
      "requested_amount": 50.00,
      "available_balance": 25.50,
      "pending_balance": 5.00,
      "action": "Request a smaller amount or wait for pending cashback to be confirmed."
    }
  }
}
```

### 422 Unprocessable Entity – Payout Policy Violation

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Payout request violates withdrawal policy.",
    "details": {
      "violations": [
        "Minimum payout amount is 10.00. Requested: 5.00.",
        "Monthly payout limit (100.00) would be exceeded. Already paid this month: 95.00."
      ],
      "action": "Increase request amount and ensure monthly limit is not exceeded."
    }
  }
}
```
