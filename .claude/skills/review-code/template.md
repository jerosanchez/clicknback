---
# template.md for review-code (not typically used for this skill)
---

# Code Review Template

Use the checklist in `index.md` directly. For each violation found:

```
❌ [Category]: [Issue]
   Location: [file:line]
   Problem: [What's wrong]
   Fix: [Suggested remedy]
   Reference: [Rule/ADR]
```

Example output:

```
❌ Architectural Violation: Business logic in API layer
   Location: app/merchants/api.py:42
   Problem: Service called via `service.create` in route handler; validation in handler
   Fix: Move validation to service; keep handler to HTTP translation only
   Reference: ARCHITECTURE.md § Strict Layering
```
