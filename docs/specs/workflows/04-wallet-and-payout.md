# Workflow 4 — Wallet and Payout

> **Goal:** Check a user's wallet balance and request a cashback withdrawal.
>
> **Who runs this:** User (to check and request), Admin (to process).
>
> **Pre-condition:** At least one confirmed purchase with cashback > 0 exists for the user (Workflow 3).
>
> **HTTP file:** [`http/04-wallet-and-payout.http`](http/04-wallet-and-payout.http)
>
> **Note:** These endpoints are **backlog** features — fully specified but not yet implemented.

---

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    actor Admin
    participant API as ClickNBack API
    participant DB as Database

    User->>API: POST /api/v1/auth/login
    API-->>User: 200 OK · access_token

    User->>API: GET /api/v1/users/{user_id}/wallet
    API->>DB: Aggregate wallet balances for user
    DB-->>API: {pending, available, paid}
    API-->>User: 200 OK · {pending, available, paid}

    User->>API: GET /api/v1/users/{user_id}/wallet/transactions?page=1&page_size=10
    API->>DB: Query ledger entries for user
    DB-->>API: paginated transaction list
    API-->>User: 200 OK · {items: [{type, amount, status, reference}, ...]}

    User->>API: POST /api/v1/users/{user_id}/payouts<br/>{amount}
    API->>DB: Verify amount ≤ available balance
    alt sufficient balance
        API->>DB: Insert payout (status: "pending")<br/>Deduct from available → processing
        DB-->>API: payout record
        API-->>User: 201 Created · {id, amount, status: "pending"}
    else insufficient balance
        API-->>User: 422 Unprocessable Entity · BUSINESS_RULE_VIOLATION
    end

    User->>API: GET /api/v1/users/{user_id}/wallet
    API->>DB: Aggregate wallet balances
    DB-->>API: updated balances
    API-->>User: 200 OK · {pending, available (decreased), paid}

    Admin->>API: POST /api/v1/auth/login
    API-->>Admin: 200 OK · access_token

    Admin->>API: GET /api/v1/payouts?status=pending&page=1&page_size=10
    API->>DB: Query pending payouts
    DB-->>API: paginated payout list
    API-->>Admin: 200 OK · {items: [...]}

    alt Admin approves payout
        Admin->>API: PATCH /api/v1/payouts/{payout_id}/status<br/>{status: "approved"}
        API->>DB: Update payout status → "paid"<br/>Move amount from processing → paid
        DB-->>API: updated payout
        API-->>Admin: 200 OK · {status: "paid"}
    else Admin rejects payout
        Admin->>API: PATCH /api/v1/payouts/{payout_id}/status<br/>{status: "rejected"}
        API->>DB: Update payout status → "rejected"<br/>Return amount from processing → available
        DB-->>API: updated payout
        API-->>Admin: 200 OK · {status: "rejected"}
    end

    User->>API: GET /api/v1/users/{user_id}/wallet
    API->>DB: Aggregate wallet balances
    DB-->>API: final balances
    API-->>User: 200 OK · {pending, available, paid (increased if approved)}
```

---

## Steps

| # | Action | Endpoint |
| --- | --- | --- |
| 1 | (User) Login | `POST /api/v1/auth/login` |
| 2 | View wallet summary (pending, available, paid balances) | `GET /api/v1/users/{user_id}/wallet` |
| 3 | List wallet transactions | `GET /api/v1/users/{user_id}/wallet/transactions` |
| 4 | Request a payout (withdrawal) | `POST /api/v1/users/{user_id}/payouts` |
| 5 | (Admin) Login | `POST /api/v1/auth/login` |
| 6 | List all pending payouts | `GET /api/v1/payouts?status=pending` |
| 7 | Process (approve or reject) a payout | `PATCH /api/v1/payouts/{payout_id}/status` |
| 8 | (User) Verify wallet balances after processing | `GET /api/v1/users/{user_id}/wallet` |

## What to Expect

- The wallet has three balance buckets:
  - **pending** — cashback earned from purchases that are confirmed but not yet withdrawable (subject to a holding period in production).
  - **available** — cashback that the user can withdraw right now.
  - **paid** — total amount already withdrawn in past payouts.
- A payout request moves funds from `available` to a `processing` state.
- When the admin processes (approves) the payout, the `paid` balance increases and `processing` decreases.
- A rejected payout returns funds back to `available`.

---

_Back to [End-to-End Workflows](end-to-end-workflows.md)_
