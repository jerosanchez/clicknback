# Domain Glossary

A list of key domain terms and their definitions to clarify business concepts for new readers.

---

## A

### Active Offer

An offer that is currently valid and can be used to calculate cashback for purchases. An offer becomes active when its start date is reached and remains active until its end date passes.

### Admin (Administrator)

An authenticated user with elevated privileges who can perform administrative operations, including: creating merchants, defining offers, confirming/reversing purchases, and processing payouts. Distinguished from regular users through role-based access control.

### Available Balance

The amount of cashback funds in a user's wallet that is ready for withdrawal. Funds move from pending balance to available balance when a purchase is confirmed by an admin.

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

## I

### Idempotency

A business guarantee that submitting the same purchase request multiple times (e.g., due to network retries) produces the same result without creating duplicate purchases. Critical for reliable purchase ingestion from external systems. The system identifies duplicates by a unique external purchase ID.

---

## M

### Merchant

A partner business that offers cashback incentives on purchases made by users. Merchants are created and managed by admins and can define multiple offers over time.

### Merchant Activation

The process of enabling a merchant in the system so their offers can accept new purchases. A merchant may be deactivated to prevent new purchases while maintaining historical data.

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

### Purchase

An event representing a user transaction at a merchant. Purchases are submitted by external systems via the ingestion API and enter the system with status `pending`. Associated with: a user, a merchant, an amount, and a unique external identifier.

### Purchase Ingestion

The process by which an external system (e.g., affiliate tracking platform) submits purchase events to ClickNBack. Validates user existence, merchant existence, and external ID uniqueness to prevent duplicates. Creates purchase and cashback records.

### Purchase Reversal

An admin action that cancels a purchase and its associated cashback transaction. Sets purchase status to `reversed` and adjusts wallet balances accordingly. Can occur on purchases in any state (pending or confirmed).

---

## R

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
