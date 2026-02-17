# Security Strategy

## 1. Overview

ClickNBack handles sensitive financial data (cashback balances, transactions, payouts) and must prevent unauthorized access, data tampering, and fraudulent operations. Security is integrated into every layer: authentication of users, authorization of operations, prevention of abuse, and consistency of financial state.

This document outlines our strategic approach to authentication, authorization, financial consistency, and fraud control.

---

## 2. Authentication: Stateless, Scalable Design

ClickNBack uses **token-based stateless authentication** to enable:

- **Scalability:** Token validation is O(1) and requires no shared session state
- **Statelessness:** Any server instance can validate any token without database lookups
- **API-native design:** Bearer tokens in Authorization headers fit REST patterns naturally
- **Third-party integration:** Standard token-based auth supports webhooks, partner APIs, and mobile clients

### 2.1 Authentication Flow

1. User registers with email and password
2. User authenticates with credentials and receives a token
3. Token is included in subsequent requests (Authorization header)
4. Server validates token signature and expiration without database lookups

### 2.2 Token Design

Tokens encode:

- **User ID:** Identifies the requester
- **Role:** User or Admin, used for authorization checks
- **Expiration:** Limits exposure window if token is leaked (15-30 minute lifetime)
- **Issued-at:** Enables immediate revocation on password change (all prior tokens rejected)

### 2.3 Security Strategy

- **Short lifetime:** Tokens expire quickly; stolen tokens have limited usefulness
- **Revocation via issued-at:** Password changes invalidate all prior tokens without database queries
- **Stateless validation:** No session storage; horizontal scaling with no shared state

---

## 3. Authorization: Role-Based Access Control (RBAC)

### 3.1 Roles

ClickNBack defines two roles with clear separation:

- **User:** Standard user who earns and withdraws cashback
- **Admin:** Operator who manages merchants, offers, and system operations

### 3.2 Access Control Model

Authorization is enforced at the endpoint level:

- **Public endpoints:** User registration (no authentication required)
- **User endpoints:** Require valid JWT and role verification
- **Admin endpoints:** Require admin role, checked before service logic executes

### 3.3 Principle: Fail Fast

Authorization checks happen early:

1. Request arrives
2. JToken is validated (syntax, signature, expiration)
3. Role is extracted and checked against endpoint requirements
4. Request is rejected immediately if unauthorized (before any business logic runs)

This prevents unauthorized users from even reaching service layers.

---

## 4. Data Consistency & Financial Correctness

In a financial system, consistency is non-negotiable. ClickNBack uses multiple strategies to ensure correctness:

### 4.1 Transaction Boundaries

All financial operations (purchases, cashback confirmations, payouts) happen within database transactions:

- **Atomicity:** Either all updates succeed or all fail
- **Isolation:** Concurrent transactions don't interfere with each other
- **No partial updates:** Wallet states are never inconsistent (e.g., pending balance reduced but available not increased)

### 4.2 External ID Idempotency

Purchases and payouts use **external IDs** (from partner systems) as idempotency keys:

- **Problem solved:** If a purchase is submitted twice (network retry), it shouldn't create duplicate cashback
- **Implementation:** Unique database constraint on external ID prevents duplicates
- **Consequence:** Re-running the operation is safe; it returns the same result without side effects

### 4.3 Wallet State Transitions

Wallet states are strictly managed:

- Purchase creates **pending** balance (not yet confirmed by merchant)
- Merchant confirmation moves balance from **pending** to **available**
- User withdrawal moves balance from **available** to **paid**

Each transition validates preconditions (sufficient balance, valid state) and happens atomically.

### 4.4 Concurrency Protection

Concurrent cashback confirmations or withdrawals could cause double withdrawals. We prevent this via:

- **Row-level locking (SELECT FOR UPDATE):** Lock the wallet row while updating
- **Optimistic locking (version fields, future):** Add version field to wallet; updates fail if version changed since read
- **Serializable transactions (future):** Use SERIALIZABLE isolation level for highest safety

---

## 5. Fraud Prevention & Abuse Control

ClickNBack runs in a financial context where fraud is a real concern. We include multiple safeguards:

### 5.1 Purchase Ingestion Safeguards

- **Unique external ID enforcement:** Prevents duplicate submissions
- **Amount validation:** Rejects nonsensical amounts (negative, extreme)
- **Merchant and offer validation:** Purchase must be for an active offer
- **Timestamp validation:** Rejects purchases with timestamps far in the past/future

### 5.2 Monthly Caps

Offers define per-user monthly cashback caps:

- **Calculation:** Tracks cumulative cashback per user per month
- **Enforcement:** Rejects purchases that exceed the cap
- **Prevention:** Prevents users from gaming the system via many small purchases

### 5.3 Rate Limiting (Future)

As the system grows:

- **Per-user purchase rate:** Limit purchases per user per minute
- **Per-merchant purchase rate:** Limit purchases per merchant per hour
- **Payout rate:** Limit withdrawal frequency to prevent rapid draining

### 5.4 Fraud Detection Signals (Future)

Early warning signs that warrant investigation:

- Sudden spike in purchases from single user
- Pattern of approvals immediately followed by reversals
- User withdrawals at maximum allowed amounts
- Activity from unusual geographic locations (if timestamp enriched with location)

### 5.5 Admin Oversight

Only admins can:

- Create merchants and offers
- Process payouts (initially)
- Reverse transactions
- Access audit logs

This prevents individual users from manipulating the system.

---

## 6. Data Integrity Principles

### 6.1 Immutability of Historical Records

Financial records should be immutable—transactions create new records rather than modifying old ones:

- Purchase created one, marked as reversed (not deleted)
- Cashback transaction created once, state transitions (pending → available → paid/reversed)
- Wallet balance tracked via balance fields, not cumulative of transactions

This enables accurate auditing and prevents accidental data loss.

### 6.2 External ID as Source of Truth

External IDs (from partner systems) are the canonical reference for purchases:

- ClickNBack IDs (`uuid`) are internal
- Partner IDs (external purchase IDs) are immutable references
- Lookup by external ID is fast (indexed) and reliable

This allows partners to confidently check their own ID in our system without fearing ID collision.

### 6.3 Audit Trail

All state transitions are logged:

- **What changed:** Operation type (purchase created, payment confirmed, etc.)
- **Who changed it:** User ID or system (for background jobs)
- **When it changed:** Timestamp
- **Why it changed:** Reason/context (idempotent retry, reversal reason, etc.)

Audit logs are append-only and queryable for compliance investigations.

---

## 7. Password Security

### 7.1 Requirements

User passwords must meet minimum complexity standards to resist brute-force attacks:

- **Minimum 8 characters**
- **At least one uppercase letter**
- **At least one lowercase letter**
- **At least one digit**
- **At least one special character**

### 7.2 Storage

Passwords are never stored in plaintext:

- Passwords are hashed using bcrypt (or argon2 for future)
- Hash is salted (algorithm handles this automatically)
- Hashed password is stored; plaintext is discarded
- Authentication compares incoming password's hash with stored hash

### 7.3 Comparison

Password comparison is **timing-safe** to prevent timing attacks:

- Use constant-time comparison (not `==`)
- Prevents attacker from guessing password character-by-character based on response time

---

## 8. HTTPS & Transport Security (Deployment Concern)

While ClickNBack code doesn't implement HTTPS directly, deployment must enforce:

- **All endpoints over HTTPS only** (HTTP redirects to HTTPS)
- **HSTS headers** (tell browsers to always use HTTPS for this domain)
- **TLS 1.2 or higher**
- **No mixed content** (no unencrypted assets or API calls)

Tokens are worthless if transmitted over HTTP—attacker can intercept the token and impersonate the user.

---

## 9. Known Limitations & Strategic Decisions

| Decision | Benefit | Risk | Mitigation |
| ---------- | --------- | ------ | ----------- |
| **JWT (no revocation yet)** | Stateless, fast, scales | Leaked token valid until expiration | Short expiration (15-30 min); password change invalidates (via issued-at) |
| **No refresh tokens yet** | Simpler implementation | Users must re-authenticate when token expires | Add when user experience demands longer sessions |
| **No 2FA yet** | Lower friction for registration | Admin accounts more vulnerable | Add for admin role once admin operations are mature |
| **Rate limiting future** | Simpler initial deploy | Abuse possible if system becomes popular | Monitor for abuse patterns; implement quickly if needed |
| **Monthly caps only** | Simple to understand and audit | Can't catch sophisticated fraud patterns | Add anomaly detection and audit logs for investigation |

**Scaling principle:** Start with simple, auditable safeguards. Add sophisticated fraud detection patterns as the system grows and we observe real attack patterns.

---

## 10. See Also

For implementation decisions and technical details:

- [ADR 008: JWT-Based Stateless Authentication](./adr/008-jwt-stateless-authentication.md) — Why JWT vs. sessions, PASETO, and other alternatives
- [ADR 000: Technology Stack Selection](./adr/000-technology-stack-selection.md) — Why we use FastAPI + SQLAlchemy
- [ADR 003: API Module as Composition Root](./adr/003-api-module-as-composition-root.md) — How we structure dependency injection for authorization checks
- [Product Overview](../specs/product-overview.md) — Business context and workflows
- [System Level Guarantees](../specs/system-level-guarantees.md) — Financial correctness guarantees
