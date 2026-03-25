# Workflow 5 — Admin Purchase Confirmation (Manual Approval)

> **Goal:** An admin manually reviews and confirms or rejects individual purchases, as opposed to the automatic background verification (Workflow 3).
>
> **Who runs this:** Admin
>
> **Pre-condition:** A user has recorded a purchase (Workflow 3). Admin is authenticated.
>
> **HTTP file:** [`http/05-purchase-confirmation.http`](http/05-purchase-confirmation.http)
>
> **Note:** Purchase confirmation and reversal endpoints are **backlog** features — they are designed and fully specified but not yet implemented in detail. The `.http` file documents the intended interactions against the upcoming API surface.

---

## Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    actor User
    participant API as ClickNBack API
    participant DB as Database

    User->>API: POST /api/v1/auth/login
    API-->>User: 200 OK · access_token

    User->>API: POST /api/v1/purchases<br/>{external_id, user_id (own), merchant_id, amount, currency}
    API->>DB: Insert purchase (status: "pending", cashback_amount: 0)
    DB-->>API: purchase record
    API-->>User: 201 Created · {id, status: "pending", cashback_amount: 0}

    Admin->>API: POST /api/v1/auth/login
    API-->>Admin: 200 OK · access_token

    Admin->>API: GET /api/v1/purchases?status=pending<br/>(or GET /api/v1/purchases/{purchase_id})
    API->>DB: Query purchases by status
    DB-->>API: paginated purchase list or single record
    API-->>Admin: 200 OK · {items: [...]} or {purchase object}

    Note over Admin,API: Admin reviews the purchase details<br/>(amount, merchant, date, user, etc.)

    alt Admin confirms the purchase
        Admin->>API: POST /api/v1/purchases/{purchase_id}/confirm
        API->>DB: Check purchase status is "pending"
        alt status is pending
            API->>DB: Update purchase (status: "confirmed")
            API->>EventBroker: Publish PurchaseConfirmed event
            DB-->>API: updated record
            API-->>Admin: 200 OK · {id, status: "confirmed", cashback_amount: X}
            EventBroker->>API: On PurchaseConfirmed event
            API->>DB: Fetch active offer for merchant on purchase date
            alt active offer found
                DB-->>API: offer {cashback_type, cashback_value, monthly_cap}
                API->>DB: Calculate cashback (apply monthly cap)
                API->>Wallet: Credit user wallet (amount: cashback, status: "pending")
                Wallet->>DB: Insert wallet transaction
            else no active offer
                Note over API: cashback = 0
            end
            API->>DB: Update purchase (cashback_amount: calculated)
        else status is not pending
            API-->>Admin: 409 Conflict · purchase status is not "pending"
        end
    else Admin rejects (reverses) the purchase
        Admin->>API: POST /api/v1/purchases/{purchase_id}/reverse
        API->>DB: Check purchase status is not already "reversed"
        alt status allows reversal
            API->>DB: Update purchase (status: "reversed")
            API->>EventBroker: Publish PurchaseReversed event
            DB-->>API: updated record
            API-->>Admin: 200 OK · {id, status: "reversed", cashback_amount: 0}
            EventBroker->>API: On PurchaseReversed event
            alt purchase was previously confirmed
                API->>Wallet: Debit user wallet (reverse previous cashback)
                Wallet->>DB: Insert wallet reversal transaction
            else purchase was pending
                Note over API: No wallet impact; no cashback was credited
            end
        else status does not allow reversal
            API-->>Admin: 409 Conflict · cannot reverse purchase in current state
        end
    end

    User->>API: GET /api/v1/users/{user_id}/wallet
    API->>DB: Aggregate wallet balances
    DB-->>API: {pending, available, paid}
    API-->>User: 200 OK · wallet summary (updated if confirmed)
```

---

## When to Use This Workflow

This workflow is used in two scenarios:

1. **Chargeback / Reversal Right:** A user disputes a purchase; the admin manually reverses it and returns the cashback to the wallet.

2. **Manual Oversight:** In some merchant partnerships, purchases may require manual review before confirmation (e.g., high-value transactions, fraud screening, or on-platform dispute verification) as an alternative to or in addition to the automatic background job (Workflow 3).

---

## Steps

| # | Action | Endpoint |
| --- | --- | --- |
| 1 | (Admin) Login | `POST /api/v1/auth/login` |
| 2 | (Admin) List pending purchases or view a single purchase | `GET /api/v1/purchases` or `GET /api/v1/purchases/{id}` |
| 3 | (Admin) Manually confirm or reject a purchase | `POST /api/v1/purchases/{id}/confirm` or `POST /api/v1/purchases/{id}/reverse` |
| 4 | (Admin) (Optional) View the updated purchase | `GET /api/v1/purchases/{id}` |
| 5 | (User) Verify wallet balances | `GET /api/v1/users/{user_id}/wallet` |

---

## What to Expect

### On Confirmation

- The purchase status changes from `pending` to `confirmed`.
- A `PurchaseConfirmed` event is published.
- The system looks up the active offer for the merchant at the time of purchase.
- Cashback is calculated per the offer rules (percentage or fixed amount, subject to monthly cap).
- The cashback is credited to the user's wallet as a `pending` balance.
- If no active offer exists, cashback remains `0`.

### On Reversal

- The purchase status changes to `reversed`.
- A `PurchaseReversed` event is published.
- If the purchase was previously `confirmed` (and cashback was credited), the cashback is debited from the user's wallet.
- If the purchase was still `pending` (no cashback credited yet), no wallet impact occurs.
- The user can check their wallet to verify the reversal.

### Idempotency and Conflicts

- Attempting to confirm an already-confirmed purchase returns `409 Conflict`.
- Attempting to confirm a rejected purchase returns `409 Conflict`.
- Attempting to reverse a purchase in an invalid state returns `409 Conflict`.

---

## Relationship to Workflow 3

| Aspect | Workflow 3 (Auto) | Workflow 5 (Manual) |
| --- | --- | --- |
| **Trigger** | Background job on schedule (every 60s) | Admin HTTP request |
| **Verification** | Simulated bank reconciliation | Admin review / human judgment |
| **Confidence** | Auto-confirmed or auto-rejected after retries | Explicit admin decision |
| **Use Case** | Standard purchase ingestion | Disputes, reversals, high-value oversight |
| **Wallet Impact** | Automatic on `PurchaseConfirmed` event | Admin-driven; reversed on `PurchaseReversed` event |

Both workflows can coexist. An admin may manually reverse an auto-confirmed purchase, or manually confirm a `pending` purchase before the background job runs.

---

_Back to [End-to-End Workflows](end-to-end-workflows.md)_
