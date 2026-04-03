---
# examples.md for write-adr
---

# Example: ADR-010 Async Database Layer

See `docs/design/adr/010-async-database-layer.md`:
- Clear context (sync blocks threads, limits concurrency)
- Three options (Async SQLAlchemy, external queue, thread pool)
- Decision with rationale (async SQLAlchemy chosen)
- Consequences (better concurrency, learning curve, testing complexity)

---
