# Writing Functional Specifications

This is the authoritative guide for writing functional specification (FR) documents. It covers structure, content layers, validation techniques, and common pitfalls to avoid. Every new feature must have a corresponding functional spec before implementation begins.

---

## Purpose

A functional specification document is the **single source of truth** for a feature. It describes:

- **What** the feature does and who uses it
- **When** it can be used (conditions, constraints)
- **Why** business rules matter (acceptance criteria)
- **How** the user interacts with it (scenarios, flows)

The spec is **implementation-agnostic** — it does not mention code, databases, API details, or technology choices. Those concerns belong in the **API contract** (a separate document) and the **code** itself.

---

## One Spec Per Feature

Write one spec per user-facing action; do not group multiple actions into a domain-area document.

**Correct:**

- "Set a Feature Flag" ✅ (one feature)
- "Delete a Feature Flag" ✅ (one feature)
- "List Feature Flags" ✅ (one feature)

**Incorrect:**

- "Feature Flags" ❌ (domain area, not a feature)
- "Admin Dashboard" ❌ (multiple features bundled)

**Naming Convention:** `XX-NN-short-name.md`

- `XX` — Two-letter domain prefix (e.g. `FF` for Feature Flags, `PU` for Purchases, `M` for Merchants, `U` for Users, `O` for Offers, `PA` for Payouts, `W` for Wallets)
- `NN` — Two-digit sequence number within the domain, starting at `01` (e.g. `01`, `02`, `03`)
- `short-name` — Kebab-case description of the single feature

**Examples:**

- `FF-01-set-feature-flag.md`
- `FF-02-delete-feature-flag.md`
- `FF-03-list-feature-flags.md`
- `PU-01-purchase-ingestion.md`
- `M-01-merchant-creation.md`

---

## Mandatory Section Order

Every functional spec must include these sections **in this exact order**:

### 1. Title and Preamble

```markdown
# XX-NN: Feature Name

IMPORTANT: This is a living document, specs are subject to change.
```

Keep it brief and specific. Use active voice: "User Login", not "Login Functionality".

### 2. User Story

```markdown
## User Story

_As a <role>, I want to <action> so that <benefit>._
```

Write it as a single sentence in the given–want–benefit format. This is the compass — all design decisions check against it.

**Role:** Who uses this feature? (e.g., "a registered user", "an admin", "an external system")
**Action:** What do they do? (e.g., "authenticate", "create a flag")
**Benefit:** Why does it matter? (e.g., "obtain an access token", "control feature rollout")

---

### 3. Domain Concepts (Optional)

If the feature introduces unfamiliar terms or domain boundaries, add a table:

```markdown
## Domain Concepts

| Term | Description |
| --- | --- |
| **Flag key** | A unique string identifier for the feature, e.g. `purchase_confirmation_job` |
| **Scope type** | `global` (applies platform-wide), `merchant` (applies to one merchant), or `user` (applies to one user) |
```

Explain each term once, clearly. Developers will reference this when reading acceptance criteria and use cases.

**When to include:** Only if the feature uses domain terms unfamiliar to a new developer.

**When to skip:** For simple features like "User Login" or "Merchant Activation" where the terms are obvious.

---

### 4. Constraints

Include every input validation rule, authorization check, and data dependency in this section — it is the most critical part of the spec. Constraints encode all business rules, input validation, authorization, and data logic that shape the feature.

Organize constraints by category:

```markdown
## Constraints

### Authorization Constraints

- Only authenticated admin users can create feature flags.
- Users may only ingest purchases on behalf of themselves (cannot ingest for another user).

### Input Constraints

- `key` must be non-empty, lowercase `snake_case`, and no longer than 100 characters.
- `amount` must be a positive number (greater than zero).
- `scope_id` is required when `scope_type` is `merchant` or `user`, and must be a valid UUID.
- `scope_id` must be `null` (or omitted) when `scope_type` is `global`.
- Email must be in valid email format; leading/trailing whitespace is stripped.

### Data Constraints

- Exactly one record per `(key, scope_type, scope_id)` triple is enforced via a database unique constraint.
- A valid offer must be available for the merchant for today's date.
- The system resolves the offer automatically; the caller does not provide `offer_id`.

### Behavior Constraints

- Requests must be idempotent: re-submitting the same `external_id` yields a conflict response (no duplicate).
- Account lockout (429 Too Many Requests) is not currently implemented — that is deferred to a future release.
```

**Key guidance:**

- Be exhaustive. Every input validation rule, every authorization check, every data dependency goes here.
- Use clear bullet points. Avoid paragraphs.
- Call out deferred work explicitly ("NOT IMPLEMENTED YET", "deferred to a future release").
- Do not embed how to check a constraint ("the system will query the database") — only what the constraint is.

**Common mistake:** Omitting constraints because they "should be obvious". They are not. A missing constraint causes ambiguity in tests, leading to confusion and bugs.

---

### 5. BDD Acceptance Criteria

Use BDD syntax to describe each scenario in which the feature succeeds or fails:

```markdown
## BDD Acceptance Criteria

**Scenario:** Successful authentication with valid credentials
**Given** I have correct email and password
**When** the user account exists and credentials are valid
**Then** a valid JWT token is issued

**Scenario:** Authentication with non-existent user
**Given** I attempt to login with an email that is not registered
**When** the system attempts to validate credentials
**Then** an authentication error is returned

**Scenario:** Authentication with incorrect password
**Given** I attempt to login with correct email but wrong password
**When** the system validates the password
**Then** an authentication error is returned
```

**Mandatory coverage:**

Every functional spec must include at least one scenario for each of these categories:

| Category | Minimum scenarios | Coverage |
| --- | --- | --- |
| Happy path | ≥1 | The feature works as intended |
| Authorization failure | ≥1 | Unauthenticated (`401`) or non-admin (`403`) |
| Validation failure | ≥1 | Invalid input (e.g., malformed email, negative amount) |
| Business rule failure | ≥1 | Constraint violated (e.g., non-existent user, inactive merchant) |
| Conflict/idempotency | Varies | If applicable (e.g., duplicate external_id) |

**Per-scenario rules:**

1. **Given** — State the precondition: what is true before the action.
2. **When** — State the trigger: what the user does or what event occurs.
3. **Then** — State the expected outcome: what the result is.

Keep each scenario short: one **Given**, one **When**, one **Then** per scenario. If a scenario requires multiple steps, break it into numbered steps within the **Then** clause:

```markdown
**Scenario:** User updates their profile
**Given** I am authenticated
**When** I submit new profile data
**Then**
1. The profile is updated in the database
2. The user is returned the updated profile
3. A confirmation email is sent (if email is changed)
```

**How to write good scenarios:**

- Use concrete examples in **Given** (specific error codes, specific UUIDs from seed data) rather than abstract placeholders.
- Keep each scenario independent; never assume state from previous scenarios.
- Cover the happy path first, then auth failures, then validation failures, then business-rule failures.
- List scenarios in order of **likelihood**/**importance**: happy path first, then most common sad paths.

---

### 6. Use Cases

Write use cases as **step-by-step numbered flows** in prose. They answer the question: "How does the system actually execute this feature?"

**Structure:**

```markdown
## Use Cases

### Happy Path

Descriptive heading (e.g., "User successfully authenticates with valid credentials")

1. User submits email and password.
2. System validates email format.
3. System retrieves user by email.
4. System validates credentials against stored hash.
5. System issues access token.
6. System returns the access token.

### Sad Paths

#### Descriptive heading (first sad path)

1. User submits invalid email and password.
2. System validates email format.
3. System detects invalid email format.
4. System rejects the request with validation error `VALIDATION_ERROR`.

#### Descriptive heading (second sad path)

1. User submits email and password.
2. System validates email format.
3. System retrieves user by email.
4. System finds user does not exist.
5. System rejects the request with error code `USER_NOT_FOUND`.
```

**Key guidance:**

- Number each step. Use numbered lists, not bullet points.
- Include error codes in the flow where validation fails or a business rule is violated (e.g., `VALIDATION_ERROR`, `USER_NOT_FOUND`).
- Each use case should trace a complete flow from input to output.
- Use past tense for observed events ("System finds user does not exist") and present tense for system actions ("System rejects the request").

**Happy Path:** The feature works correctly under ideal conditions.

**Sad Paths:** One sub-section per distinct failure mode. Each sad path is a complete flow that demonstrates a constraint violation or error.

---

### 7. API Contract Reference

Link to the corresponding API contract document. This is the **only place** in the functional spec where you mention HTTP details:

```markdown
## API Contract

- [Authenticate user, return JWT](../../../design/api-contracts/auth/login.md)
```

Or if there are multiple endpoints:

```markdown
## API Contract

- [Create Feature Flag](../../../design/api-contracts/feature-flags/set-feature-flag.md)
- [List Feature Flags](../../../design/api-contracts/feature-flags/list-feature-flags.md)
- [Delete Feature Flag](../../../design/api-contracts/feature-flags/delete-feature-flag.md)
```

The API contract file contains endpoint paths, HTTP methods, status codes, JSON request/response bodies, and headers. Keep all of that detail out of the functional spec.

---

## Validation Checklist

Before committing a functional spec, verify the following:

- [ ] **One feature per document** — Does the spec describe exactly one user-facing action?
- [ ] **Naming follows convention** — Is the filename `XX-NN-short-name.md`?
- [ ] **All mandatory sections present** — Are Title, User Story, Constraints, BDD Acceptance Criteria, Use Cases, and API Contract all present in order?
- [ ] **Constraints are exhaustive** — Can a developer set up a test case from the constraints alone without asking clarifying questions?
- [ ] **BDD Acceptance Criteria are specific** — Are there concrete examples, not vague placeholders?
- [ ] **Minimum coverage met** — Does the spec include at least one happy path, one auth failure, one validation failure, and one business-rule failure?
- [ ] **Use cases trace complete flows** — Can a developer implement the feature by following the steps?
- [ ] **Error codes are included** — Do the use cases mention error codes (e.g., `USER_NOT_FOUND`) for each failure branch?
- [ ] **API Contract link is valid** — Does the linked file exist and correspond to this feature?
- [ ] **No implementation details** — Does the spec avoid mentions of: code files, class names, database tables, ORM models, HTTP verbs, JSON fields, status codes, or technology names?
- [ ] **No duplication** — Does the spec avoid repeating the same rule in both Constraints and Use Cases?
- [ ] **Spelling and grammar** — Is the text correct, readable, and consistent in voice?

---

## Common Mistakes

### 1. **Mixing Functional Spec with API Contract**

**Wrong:**

```json
The feature returns:

{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "...",
    "details": {...}
  }
}
```

**Correct:** Mention the error code in a use case step:

```text
System rejects the request with error code USER_NOT_FOUND.
```

Then provide the exact JSON in the API Contract document.

---

### 2. **Vague Constraints**

**Wrong:**
> The email must be valid.

**Correct:**
> Email must be in valid email format (RFC 5322 subset); leading/trailing whitespace is stripped.

---

### 3. **Incomplete Authorization Rules**

Many specs forget to spell out who can do what.

**Wrong:** No authorization section.

**Correct:**

```markdown
### Authorization Constraints

- Only authenticated admin users can set feature flags.
- Users may only view their own purchase history.
- Merchants may only view offers they created.
```

---

### 4. **Mixing Happy and Sad Paths in One Scenario**

**Wrong:**

```markdown
**Scenario:** Create a flag or show error
**Given** I am an admin
**When** I send a request
**Then** either the flag is created or an error is shown
```

**Correct:**

```markdown
**Scenario:** Admin successfully creates a flag
**Given** I am an admin
**When** I send a valid request with key, enabled, and scope_type
**Then** the flag record is created and returned

**Scenario:** Invalid scope-type value
**Given** I am an admin
**When** I send a request with `scope_type: invalid_value`
**Then** a validation error is returned with code VALIDATION_ERROR
```

---

### 5. **Use Cases That Don't Match Scenarios**

**Wrong:** The use case describes a path that no scenario exercises.

**Correct:** Every use case path (happy path and all sad path branches) has at least one corresponding scenario.

---

### 6. **Forgetting to Call Out Deferred Work**

**Wrong:** The spec is silent about features that might exist in the future.

**Correct:**

```markdown
> **Note:** Account lockout (e.g., 423 Locked) and rate limiting (429 Too Many Requests)
> are not currently implemented. These may be added in a future release as security
> requirements evolve.
```

---

## Examples

Well-formed functional specs serve as templates for future work. See these examples in the repository:

- [A-01: User Login](../specs/functional/auth/A-01-user-login.md) — Simple happy path with clear sad paths
- [FF-01: Set Feature Flag](../specs/functional/feature-flags/FF-01-set-feature-flag.md) — Complex domain concepts, idempotency, multiple scopes
- [PU-01: Purchase Ingestion](../specs/functional/purchases/PU-01-purchase-ingestion.md) — Multi-step orchestration, cross-module validation, detailed use cases

Study them. Use them as templates.

---

## Writing Checklist

Use this checklist as you draft:

1. **Draft the title and user story** — Clarify exactly what feature you're documenting.
2. **Make a list of all constraints** — What inputs are valid? Who can use this? What data must exist? What is not allowed?
3. **Sketch happy path scenarios** — What does success look like? Write 1–2 scenarios.
4. **Sketch sad path scenarios** — What can go wrong? Write 1–2 scenarios per category (auth failure, validation failure, business-rule failure).
5. **Fill in the BDD table** — Convert your sketches into Gherkin Given–When–Then format. Make them concrete with examples.
6. **Trace the happy path use case** — Write numbered steps from input to output. Include error codes for failures.
7. **Trace sad path use cases** — One per distinct failure mode.
8. **Add domain concepts table** — If needed.
9. **Draft API contract link** — You may draft it in parallel or immediately after this spec.
10. **Review against the validation checklist** — Fix any gaps.

---

## Next Steps

After writing a functional spec:

1. **Create or update the corresponding API Contract** — Do this before implementation begins. See `docs/design/api-contracts/` and the API Contract section in `docs/guidelines/feature-documentation.md` for the format.
2. **Get human review** — Have someone read the spec and ask clarifying questions. If they have to ask, the spec is incomplete.
3. **Use the spec to drive implementation** — Each step in the use cases maps to code; each scenario guides a test case.
4. **Keep it living** — Update the spec if business rules change. It is not a frozen artifact; it evolves with the product.
