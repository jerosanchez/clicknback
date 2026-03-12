# ADR-017: Fixed-Interval Retry Strategy for Background Jobs

## Status

Accepted

## Context

Background jobs in ClickNBack follow the Fan-Out Dispatcher + Per-Item Runner pattern described in [ADR-016](016-background-job-architecture-pattern.md). Each runner drives a single item through up to a configurable number of attempts. Between soft failures the runner must sleep before the next attempt. The duration of that sleep — the *retry interval* — is a design decision that applies to every background job in the application.

Several strategies exist:

| Strategy | Interval formula (attempt `n`) | Characteristics |
| --- | --- | --- |
| **Fixed interval** | `base` | Predictable, simple to configure and reason about. |
| **Linear backoff** | `base × n` | Moderate ramp-up; still bounded and predictable. |
| **Exponential backoff** | `base × 2^(n-1)` | Used by most major cloud providers; gives the remote system progressively more time to recover. |
| **Exponential + jitter** | `random(0, base × 2^(n-1))` | Prevents the *thundering herd* problem when many items fail simultaneously. |

The choice interacts with the scheduler tick period, the maximum-attempts cap, and observability: a predictable retry schedule makes log timestamps easy to read during manual smoke-testing.

## Decision

All background job runners in this MVP use a **fixed retry interval**. The runner sleeps exactly `retry_interval_seconds` between every consecutive attempt, regardless of how many prior attempts have failed.

```text
attempt 1        attempt 2        attempt 3
   |── base sleep ──|── base sleep ──|── force-settle
```

For the purchase verification job specifically, `retry_interval_seconds` is bound to `PURCHASE_CONFIRMATION_INTERVAL_SECONDS` (default: 60 s) — see `app/purchases/composition.py`.

When additional background jobs are introduced (e.g. payout settlement, notification dispatch) they should follow the same convention: one `*_interval_seconds` config key per job, reused as both the scheduler tick period and the per-item retry sleep.

## Rationale

1. **Single config knob per job.** The scheduler tick and the retry sleep share the same value. The mental model is simple: "one pending item gets one verification attempt per tick."

2. **Smoke-test friendliness.** With a 60-second fixed interval and 3 attempts, the full rejection path completes in roughly 3 minutes — predictable enough to follow without guessing when the next attempt will fire.

3. **Proportionate complexity for an MVP.** All current external integrations are simulated (e.g. `SimulatedPurchaseVerifier`). Simulated gateways either succeed on the first attempt or never succeed at all; an adaptive backoff strategy would add complexity without changing any observable outcome.

4. **No thundering-herd risk at current scale.** With a single event loop and an in-memory in-flight tracker there is no concurrent process that could produce a retry storm.

## How to Evolve This When Needed

When a real external service is integrated, revisit the retry strategy for that specific job runner. The upgrade options below are listed in order of increasing complexity. All changes are local to the runner's sleep expression and the composition / config layer — the dispatcher, processor, verifier, and in-flight tracker are untouched, which is a direct benefit of the ADR-016 architecture.

### Option A — Linear backoff (low effort)

Change `asyncio.sleep(retry_interval_seconds)` to `asyncio.sleep(retry_interval_seconds * attempt)`. No new configuration needed. Total wait before exhaustion grows from `(n-1) × base` to `sum(1..n-1) × base`.

### Option B — Exponential backoff (medium effort)

```python
sleep_seconds = retry_interval_seconds * (2 ** (attempt - 1))
await asyncio.sleep(sleep_seconds)
```

Introduce a separate `retry_base_interval_seconds` config key so the scheduler tick and the base backoff can be tuned independently. Cap the result at a `retry_max_interval_seconds` ceiling to prevent unbounded waits.

### Option C — Exponential backoff with full jitter (recommended for production)

```python
cap = min(retry_max_interval_seconds, retry_base_interval_seconds * (2 ** (attempt - 1)))
sleep_seconds = random.uniform(0, cap)
await asyncio.sleep(sleep_seconds)
```

Full jitter (uniform random in `[0, cap]`) is the strategy recommended by AWS and most distributed-systems literature for avoiding correlated retry storms. It requires `retry_base_interval_seconds` and `retry_max_interval_seconds` config keys and an injected random-number source for testability.

## Alternatives Considered

**Exponential backoff from the start** — rejected: adds a second config knob and makes the smoke-test timeline harder to reason about, with no observable benefit given the simulated gateways.

**Letting the dispatcher tick drive retries** (i.e. no inner sleep — exit and let the next tick re-enqueue) — rejected: this was explicitly evaluated and discarded in [ADR-016](016-background-job-architecture-pattern.md); it ties retry cadence to the scheduler interval and loses per-item retry control.

## Consequences

- The retry interval is not adaptive; a transient outage that resolves in 30 seconds will still wait the full base sleep. Acceptable for simulated gateways.
- The total settlement window is fully predictable: `(max_attempts - 1) × interval_seconds`. This makes smoke-test guides straightforward to write.
- Migrating any individual job runner to exponential backoff is a localised, low-risk change that does not affect other jobs or shared infrastructure.

## References

- [ADR-013: Async Purchase Confirmation](013-async-purchase-confirmation.md)
- [ADR-016: Background Job Architecture Pattern](016-background-job-architecture-pattern.md)
- `app/purchases/jobs/verify_purchases/_runner.py`
- `app/purchases/api-requests/verify-purchases-job.http`
