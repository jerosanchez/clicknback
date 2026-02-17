# Testing Strategy

## 1. Overview

ClickNBack adopts a **layered testing strategy** using a disciplined test pyramid: many fast unit tests, some integration tests, and few end-to-end tests.

This approach balances **fast developer feedback** on business logic with **practical confidence** in data handling and user workflows, while avoiding the maintenance burden of over-testing implementation details.

---

## 2. The Test Pyramid

- **Unit Tests (Many):** Service logic, API error handling, policies/validators. Mocked dependencies, instant feedback. Runs on every commit (local and CI).
- **Integration Tests (Some):** Service + database interactions. Real data persistence, slower but catches data layer issues. Runs in CI after unit tests pass.
- **End-to-End Tests (Few):** Complete user workflows. Validates entire system works, slow but covers critical paths. Runs in CI before deployment or on release branches.

**Philosophy:** Test business logic and contracts thoroughly; let higher layers catch integration issues rather than over-testing thin wrappers. Fast unit tests provide immediate feedback to developers; integration and E2E tests validate systems work end-to-end.

---

## 3. Strategic Decisions

### 3.1 What We DO Test

- **Service layer:** Business logic in isolation (happy paths, exceptions, edge cases)
- **API layer:** Error responses and status codes only (happy paths covered by E2E tests)
- **Policies & validators:** Domain rules as pure functions (password complexity, calculation rules, constraints)

### 3.2 What We DON'T Test (And Why)

- **Thin repositories:** Query wrappers that simply forward to ORM. These are implementation details—bugs surface in integration or E2E tests. Testing them requires a test database and adds maintenance burden with low ROI.
- **Happy path API responses:** Covered more effectively in E2E tests. Unit testing them would duplicate work without additional value.

This selective approach keeps the test suite focused and maintainable as ClickNBack grows.

---

## 4. Code Coverage: Approach & Targets

### 4.1 Why Coverage Matters

Code coverage measures what percentage of the codebase is exercised by tests. It's a proxy for risk: untested code paths may contain bugs, especially in financial systems like ClickNBack where correctness is non-negotiable.

However, coverage is **not a goal in itself**—it's a diagnostic tool. 90% coverage with weak tests is worse than 70% coverage with strong tests.

### 4.2 Targets by Layer

Only for reference, keep this figures in mind:

| Layer | Target | Rationale |
| ------- | -------- | ----------- |
| **Services** | 85%+ | Core business logic; high risk if untested |
| **Policies** | 95%+ | Pure business rules; easy to test comprehensively |
| **Repositories** | 40-50% | Query wrappers; covered by integration tests |
| **API handlers** | 70%+ | Error paths tested; happy paths in E2E tests |
| **Overall project** | 75%+ | Reasonable threshold given strategic decisions |

### 4.3 Critical Paths: 100% Coverage

Certain areas demand complete coverage due to financial sensitivity:

- **Cashback calculation:** All formulas, caps, edge cases
- **Wallet operations:** Balance updates, concurrency handling
- **State transitions:** Pending → confirmed → paid flows
- **Fraud prevention:** Idempotency checks, duplicate detection

### 4.4 Coverage as a Development Practice

Coverage reports guide testing efforts during code review:

- New code without coverage is questioned
- Dropping coverage triggers investigation
- Patterns in uncovered code highlight risky assumptions

---

## 5. Quality Standards

### 5.1 For Contributors

Before submitting code:

- All new code has corresponding tests
- All tests pass
- Coverage met: Verify new code is covered (aim for 75%+)
- Code is formatted

### 5.2 Test Code Standards

Test code requires the same rigor as production code:

- **Clarity:** Test intent should be obvious within 10 seconds
- **Isolation:** Each test is independent; shared state creates flaky tests
- **Maintainability:** Use factories and fixtures; avoid duplication
- **Speed:** 99% of tests should run in < 100ms (fast feedback loop)
- **Naming:** Test names describe behavior, not test IDs
  - ✅ `test_create_user_raises_exception_on_duplicate_email`
  - ❌ `test_create_user_2`

---

## 6. Known Limitations & Trade-offs

This strategy makes deliberate trade-offs. Understanding them shows pragmatism:

| Decision | Benefit | Risk | Mitigation |
| ---------- | --------- | ------ | ------------ |
| **Skip thin repository unit tests** | Fast suite, low maintenance burden | Query bugs caught later | Integration tests when system grows |
| **Skip API happy path unit tests** | Avoid duplication, focus on contracts | Endpoints assumed correct | E2E tests validate real workflows |
| **Extensive mocking in unit tests** | Isolated, fast tests, quick feedback | May miss integration issues | Integration tests catch cross-layer bugs |
| **No integration tests yet** | Simpler initial setup, faster development | Data layer untested | Add when multi-service workflows emerge |

**Scaling principle:** As ClickNBack grows, integration and E2E tests expand coverage. The pyramid inverses—unit tests provide foundation, integration tests catch layer interactions, E2E tests validate user journeys.

---

## 7. See Also

For implementation details and design rationale:

- [ADR 007: Layered Testing Strategy](./adr/007-layered-testing-strategy.md) — Explains why we make these decisions
- [Architecture Overview](./architecture-overview.md) — System design context
