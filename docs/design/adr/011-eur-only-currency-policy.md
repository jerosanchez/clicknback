# ADR 011: EUR-Only Currency Policy

## Status

Accepted

## Context

Purchase ingestion requires a `currency` field so that the platform can record
the denomination of each transaction. The field was introduced to acknowledge that
currency is an important attribute of a purchase and to leave room for
multi-currency support in the future.

During the initial implementation, a full ISO 4217 currency validator was added to
the Pydantic schema (`PurchaseCreate`). This required embedding the entire set of
~180 active ISO 4217 alphabetic codes as a hardcoded `frozenset` inside the schema
module. While technically correct, this approach has several drawbacks:

- **Complexity without benefit.** The platform currently operates only in EUR.
  Accepting purchases in other currencies would require changes throughout the stack
  (cashback calculation, reporting, settlement), none of which are implemented.
  Validating the full ISO 4217 set gives no real value at this stage.
- **Maintenance burden.** ISO 4217 is updated periodically (codes are added,
  removed, and renamed). Keeping a hardcoded set accurate over time is error-prone
  without a dedicated dependency.
- **Schema vs. domain concern.** Whether a currency is *recognised by ISO 4217* is
  a schema-level formatting check. Whether a currency is *supported by the platform*
  is a business rule. These are different concerns and should live in different layers.
- **Premature library introduction.** The alternative — using a third-party package
  such as `pycountry` — would add a dependency for a feature that provides no
  business value today, and introduces its own update and security surface.

## Decision

We adopt a **EUR-only currency policy** enforced as a domain policy in the service
layer, following the same callable injection pattern already used for user, merchant,
and offer policies (see ADR 004).

The changes are:

1. **Schema** (`PurchaseCreate`): The `currency` field retains the `min_length=3,
   max_length=3` constraint so that obviously malformed inputs are rejected at the
   HTTP boundary with a standard Pydantic 422. The full ISO 4217 membership check
   and the associated `frozenset` are removed.

2. **Exception** (`UnsupportedCurrencyException`): A new domain exception is added
   to signal that the submitted currency is not accepted by the platform.

3. **Policy function** (`enforce_currency_eur`): A new policy function lives in
   `app/purchases/policies.py`. It checks `currency.upper()` against a small
   `_SUPPORTED_CURRENCIES` frozenset (currently `{"EUR"}`) and raises
   `UnsupportedCurrencyException` if the currency is not in the set. Adding a new
   currency in the future requires a one-line change to this set.

4. **Service** (`PurchaseService`): `enforce_currency_supported` is injected as a
   `Callable[[str], None]`, consistent with the existing policy injection pattern.
   It is called immediately after the duplicate-purchase check so that the expensive
   remote calls (user, merchant, offer) are not made for unsupported currencies.

5. **API** (`ingest_purchase`): `UnsupportedCurrencyException` is caught and mapped
   to a `422 UNPROCESSABLE_ENTITY` response with a clear message and the submitted
   currency in the details payload.

## Consequences

### Positive

- The codebase is simpler: no large hardcoded constant, no external dependency.
- The policy is easy to extend: adding USD requires one change in one place.
- Concern separation is clean: schema validates *shape*, policy validates *business rules*.
- Tests are precise: policy tests verify EUR behaviour; the schema tests stay focused
  on length constraints.
- The `currency` field is preserved in the data model, keeping the path to
  multi-currency support open without any rework.

### Negative / Trade-offs

- A 3-character string that is not a real currency code (e.g. `"ZZZ"`) passes schema
  validation (it has the right length) and is rejected later in the service with a 422.
  This is acceptable: the error is still caught before any side effects, and the response
  is equally informative.
- When multi-currency support is needed, the schema will need to be updated (e.g. by
  integrating `pycountry` or a similar library) in addition to the policy. This is a
  deliberate deferral, not a forgotten concern.

## Related

- ADR 004 — Use Callable Injection for Stateless Dependencies (policy injection pattern)
- PU-01 — Purchase Ingestion functional spec
- `app/purchases/policies.py` — `enforce_currency_eur`
- `app/purchases/exceptions.py` — `UnsupportedCurrencyException`
