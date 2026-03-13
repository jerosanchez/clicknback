# Domain Glossary

A list of key domain terms and their definitions to clarify business concepts for new readers.

---

## A

### Active Offer

An offer that is currently valid and can be used to calculate cashback for purchases. An offer becomes active when its start date is reached and remains active until its end date passes.

### Admin (Administrator)

An authenticated user with elevated privileges who can perform administrative operations, including: creating merchants, defining offers, confirming/reversing purchases, and processing payouts. Distinguished from regular users through role-based access control.

### Audit Trail

A persistent, queryable database record of every critical operation performed on the platform. Each entry captures who acted (actor type and ID), what they did, when, against which resource, and the outcome. Unlike application logs (which are ephemeral and subject to rotation), audit records are stored in the `audit_logs` table, survive restarts and deployments, and can be queried directly via SQL for compliance, debugging, and traceability.

### Available Balance

The amount of cashback funds in a user's wallet that is ready for withdrawal. Funds move from pending balance to available balance when a purchase is confirmed by an admin.

---

## B

### Background Job

An automated task that runs periodically on a fixed schedule without direct user or admin intervention. Background jobs handle asynchronous operations — such as purchase verification and settlement — decoupling them from the HTTP request lifecycle. Each job follows the Fan-Out Dispatcher + Per-Item Runner pattern: a dispatcher queries for pending work items and fans out to independent per-item runners, each with its own retry lifecycle.

### Bank Reconciliation

The process of verifying that a recorded purchase corresponds to a real bank movement. ClickNBack simulates this via the purchase verification background job, which periodically checks pending purchases against a simulated bank transaction record. A successful match triggers a `PurchaseConfirmed` event; exhausted retries trigger a `PurchaseRejected` event.

---

## C

### Cashback

The reward amount earned by a user from a purchase made at a participating merchant. Calculated as either a percentage of the purchase amount or a fixed amount, depending on the offer terms.

### Cashback Calculation Engine

The system component responsible for determining the cashback amount for a purchase. It applies rules including: percentage or fixed amount calculation, monthly cap enforcement, and minimum/maximum limit validation.

### Cashback Transaction

An internal financial record created when a purchase generates a reward. Tracks the state of the cashback independently from the purchase, through states: pending → available → (or) → reversed.

### Confirmation (Purchase Confirmation)

An admin action that validates a pending purchase and releases its associated cashback to the user's available balance. Triggered after merchant settlement has occurred.

---

## D

### Domain Event

An internal notification emitted when a significant state change occurs within the platform (e.g., `PurchaseConfirmed`, `PurchaseRejected`). Domain events decouple the component that causes the change from the components that react to it — cashback allocation, wallet updates, and audit logging each subscribe independently. Events are dispatched through an in-process message broker and do not require an external queue.

---

## E

### External Purchase ID

A unique identifier provided by the client when submitting a purchase. Used by the system as an idempotency key: if a request is retried, the duplicate is detected by this ID and the original response is returned without creating a second purchase. Enforced via a database-level unique constraint.

---

## F

### Fail-Open Default

The resolution behavior applied when no feature flag record exists for a given key: the system treats the feature as **enabled**. This preserves backward compatibility — features that have never been explicitly flagged continue to operate as before, and deleting a flag record re-enables the feature without any code change.

### Feature Flag

A database-backed configuration entry that allows a platform capability to be enabled or disabled at runtime without redeploying the application. Flags are identified by a string key and can be scoped globally or narrowed to a specific merchant or user. Common use cases include pausing background jobs during manual testing, disabling misbehaving features during incidents, and gating new features for a pilot subset before a full rollout.

### Flag Scope

The domain context to which a feature flag applies. Three scope types are supported: `global` (platform-wide), `merchant` (one specific merchant), and `user` (one specific user). When evaluating a flag, a scoped record takes precedence over a global record for the same key. If no record of either kind exists, the fail-open default (`enabled = true`) is returned.

---

## I

### Idempotency

A business guarantee that submitting the same purchase request multiple times (e.g., due to client-side retries) produces the same result without creating duplicate purchases. The system identifies duplicates by a unique external purchase ID.

---

## M

### Merchant

A partner business that offers cashback incentives on purchases made by users. Merchants are created and managed by admins and can define multiple offers over time.

### Merchant Activation

The process of enabling a merchant in the system so their offers can accept new purchases. A merchant may be deactivated to prevent new purchases while maintaining historical data.

### Merchant Settlement

The real-world financial process by which a merchant reconciles transactions with their payment processor after a purchase occurs. ClickNBack simulates the associated delay: purchases remain in `pending` status until the background verification job confirms the corresponding bank movement, at which point the cashback is released to the user's available balance.

### Monthly Cap

A limit on the total cashback a single user can earn from a specific merchant or offer within a calendar month. Enforced during cashback calculation to prevent excessive reward accumulation.

---

## O

### Offer

A time-bound cashback promotion defined by a merchant. Specifies: the cashback rate (percentage or fixed amount), validity dates (start and end), and a monthly cap per user. Only one active offer per merchant is typically maintained.

### Offer Activation

The process of enabling an offer so it can be used to calculate cashback. An offer becomes active on its start date and remains active until its end date is reached.

---

## P

### Paid Balance

The total amount of cashback that has been withdrawn by the user in previous payouts. Increased when a payout is completed by an admin.

### Payout

The process of transferring available cashback balance to the user. Payouts are initiated by users via a payout request, then processed by admins who can either complete or fail them.

### Payout Processing

An admin action that resolves pending payout requests. The admin can: complete the payout (increasing paid balance) or fail the payout (refunding the amount back to available balance).

### Payout Request

A user action requesting withdrawal of their available cashback balance. Creates a payout record with status `requested` that waits for admin processing.

### Pending Balance

The amount of cashback funds that a user has earned but not yet confirmed. Funds move from pending to available when a purchase is confirmed, or are removed if a purchase is reversed.

### Pending State (Purchase/Cashback)

The initial state of a new purchase or cashback transaction. Purchases become pending immediately upon ingestion; cashback remains pending until the purchase is confirmed by an admin (simulating merchant settlement delay).

### Progressive Delivery

A release strategy in which a new platform capability is enabled for a targeted subset of merchants or users before being rolled out to the entire platform. Implemented via merchant- or user-scoped feature flags, enabling canary releases, A/B tests, and pilot programmes with no code changes.

### Purchase

An event representing a user transaction at a merchant. Purchases are submitted by authenticated users via the ingestion API and enter the system with status `pending`. Associated with: a user, a merchant, an amount, and a unique external identifier.

### Purchase Ingestion

The process by which an authenticated user submits their own purchase event to ClickNBack. Validates ownership (submitter must be the purchase owner), user existence, merchant existence, and external ID uniqueness to prevent duplicates. Creates purchase and cashback records.

### Purchase Verification

The automated background process that determines whether a pending purchase should be confirmed or rejected. A background job periodically checks each pending purchase against a simulated bank movement record. Each purchase is retried up to a configurable limit; on success, a `PurchaseConfirmed` event is published; on exhaustion of retries, a `PurchaseRejected` event is published.

### Purchase Reversal

An admin action that cancels a purchase and its associated cashback transaction. Sets purchase status to `reversed` and adjusts wallet balances accordingly. Can occur on purchases in any state (pending or confirmed).

---

## R

### Rate Limiting

A control mechanism that caps the number of requests a client can make to a given endpoint within a defined time window. Applied to high-risk endpoints (purchase ingestion, login) to prevent abuse, brute-force attacks, and replay attacks. Clients that exceed the limit receive a `429 Too Many Requests` response with a `Retry-After` header.

### Reversal

See **Purchase Reversal**. The act of canceling a purchase after it has been recorded, typically due to user cancellation or fraud detection.

### Role-Based Access Control (RBAC)

A permissions model that grants access to platform features based on user role (regular user or admin). Different operations and endpoints require specific roles to prevent misuse.

---

## U

### User

An individual registered in the system who can make purchases at partner merchants and earn cashback rewards. Users maintain a wallet tracking their cashback balance across three states: pending, available, and paid.

### User Registration

The process by which a new user creates an account. Results in the user being able to authenticate and access the platform.

---

## W

### Wallet

A financial abstraction that tracks a user's cashback across three balance types: pending (awaiting confirmation), available (ready to withdraw), and paid (already withdrawn).

---
