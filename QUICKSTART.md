# Try ClickNBack: A Guided Tour

**The API is live. No account needed. No setup required.**

This page is for recruiters, hiring managers, and technical reviewers who want to experience the product before reading the code. It covers three ways to interact with the API and walks through the full cashback lifecycle — from admin login to wallet balance — in under five minutes.

For the engineering story behind what you are about to see, read [Before You Ask: What You'll Find If You Read ClickNBack](https://jerosanchez.com/posts/20260323-before-you-ask/) first. It is the guided tour of the architecture, the ADRs, and the honest tradeoffs — written for exactly this context.

---

## Option 1: Interactive (Swagger UI)

Open **<https://clicknback.com/docs>** in your browser.

Click **Authorize** at the top right and enter:

- Email: `carol@clicknback.com`
- Password: `Str0ng!Pass`

Carol is the pre-seeded admin. With her token you can list merchants, browse all offers, and see platform-wide data. To try the user side, self-register via `POST /api/v1/users` or use the pre-seeded user alice (`alice@clicknback.com` / `Str0ng!Pass`), who already has a populated wallet and purchase history.

**Suggested sequence in Swagger:**

1. `POST /auth/login` — confirm you get a JWT back
2. `GET /merchants` — see all merchants and their cashback rates
3. `GET /offers/active` — see offers visible to users (active merchant + active offer required)
4. `GET /users/me/wallet` — as alice, see the three balance buckets (pending / available / paid)
5. `POST /purchases` — ingest a purchase for alice; watch her pending balance increase
6. `GET /users/me/purchases` — see the full purchase history with cashback status per transaction

---

## Option 2: REST Client (VS Code or IntelliJ)

The file [http/quickstart.http](http/quickstart.http) in this repository walks through the same nine-step journey with inline comments explaining what each request demonstrates technically.

**Requirements:** VS Code with the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension, or IntelliJ IDEA / WebStorm (built-in HTTP client support).

Open `http/quickstart.http`, run the login steps first, paste the returned tokens into the `@adminToken` / `@userToken` variables at the top, then execute the remaining requests in order.

The file targets the live production API (`https://clicknback.com/api/v1`) so no local setup is needed.

---

## Option 3: Command Line (curl)

### Get an admin token

```bash
ADMIN_TOKEN=$(curl -s -X POST https://clicknback.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"carol@clicknback.com","password":"Str0ng!Pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### List all merchants (admin-only)

```bash
curl -s https://clicknback.com/api/v1/merchants \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
```

### Get a user token and check alice's wallet

```bash
USER_TOKEN=$(curl -s -X POST https://clicknback.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@clicknback.com","password":"Str0ng!Pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s https://clicknback.com/api/v1/users/me/wallet \
  -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool
```

### Ingest a purchase (change `external_id` on each run)

```bash
curl -s -X POST https://clicknback.com/api/v1/purchases \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "qs_curl_001",
    "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
    "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
    "amount": 75.00,
    "currency": "EUR"
  }' | python3 -m json.tool
```

---

## Seed Data Reference

The database is pre-populated and resets nightly at **03:00 UTC**.

### Users

| Email | Password | Role | Notes |
| --- | --- | --- | --- |
| `carol@clicknback.com` | `Str0ng!Pass` | admin | Platform admin; use for merchant/offer management |
| `alice@clicknback.com` | `Str0ng!Pass` | user | Pre-seeded wallet: pending 19.05, available 15.00, paid 50.00 |
| `bob@clicknback.com` | `Str0ng!Pass` | user | Has purchases including one reversal |

### Key Merchant and User IDs

These UUIDs appear in request bodies — copy them directly.

| Entity | ID |
| --- | --- |
| alice (user) | `b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d` |
| carol (admin) | `d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a` |
| Shoply (active merchant, 5% cashback) | `a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d` |
| StyleHub (active merchant, 8% cashback) | `b8c9d0e1-f2a3-4b4c-5d6e-7f8a9b0c1d2e` |

### Rate Limits

- Login and registration: **5 requests/min** per IP
- All other endpoints: **60 requests/min** per IP

_This is a shared demo environment. The database resets nightly — any data you create will not persist beyond 03:00 UTC._

---

## What to Watch For

When you ingest a purchase via `POST /purchases`, three things happen atomically in a single DB transaction: a `Purchase` row is created with `status=pending`, a `CashbackTransaction` row is created with `status=pending`, and the user's `pending_balance` in the wallet is incremented. No partial states are possible.

A background job runs on a fixed interval simulating bank reconciliation. Watch alice's purchases transition from `status=pending` to `status=confirmed` over time. When a purchase confirms, her `pending_balance` decreases and `available_balance` increases by the same cashback amount — the three-bucket model stays consistent across concurrent operations.

Try submitting the same `external_id` twice: the second call returns `409 Conflict`. That is the idempotency guarantee enforced by a `UNIQUE` constraint at the database level, not application logic.

---

## Going Deeper

If you want to move from product interaction to code review:

- **Start with the ADRs**: [`docs/design/adr/`](docs/design/adr/) — 23 decisions documented
  before implementation, including options considered and what was explicitly rejected
- **Read the tests**: [`tests/`](tests/) — 392 tests; every domain exception path is enumerated;
  write tests assert `uow.commit` is called exactly once on success
- **Read the services**: for example, [`app/purchases/services.py`](app/purchases/services.py) —
  pure business logic with no SQL, no HTTP, no JSON shapes in sight
- **Read the blog**: [Before You Ask](https://jerosanchez.com/posts/20260323-before-you-ask/) —
  the guided walkthrough of architecture, test philosophy, and financial correctness

Code review is genuinely welcome. The repository is at [github.com/jerosanchez/clicknback](https://github.com/jerosanchez/clicknback).
