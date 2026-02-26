# ClickNBack – Quality Gates

This document is the authoritative reference for code quality enforcement in the ClickNBack project. It applies to **every change** — new features, bug fixes, refactors, schema updates, policy tweaks, test additions, and documentation edits alike. No task is complete until all quality gates pass.

---

## 1. The Mandatory Command Sequence

After making any modification to the repository, run the following sequence from the project root before reporting the task as done:

```bash
make lint && make format && make test
```

All three commands must exit with code 0. If any of them fails, fix the issue and re-run the full sequence from the start. Do not stop mid-sequence or skip a gate.

---

## 2. What Each Gate Does

### `make lint`

Runs three checkers in order:

| Tool | Scope | What it enforces |
| --- | --- | --- |
| `markdownlint` | `**/*.md` | Markdown style and structure (heading hierarchy, blank lines, list formatting, line length, etc.) |
| `flake8` | `app/` | PEP 8 compliance, undefined names, unused imports, max line length of 88 characters |
| `isort --check-only` | `app/` | Import ordering (black-compatible profile, 88-char line length). Fails if imports are not sorted correctly |
| `black --check` | `app/` | Code formatting. Fails if any file would be reformatted by black |

`make lint` is read-only — it checks but does not modify files.

### `make format`

Runs the auto-formatters that fix the issues `make lint` reports:

| Tool | What it does |
| --- | --- |
| `isort` | Re-orders imports in-place under `app/` |
| `black` | Rewrites Python files in-place under `app/` to match the project's formatting standard |

Always run `make format` **before** `make lint` when fixing formatting issues. After `make format` completes, re-run `make lint` to confirm no residual issues remain.

### `make test`

Runs the full pytest suite with coverage:

```bash
python -m pytest tests/ --cov=app --cov-report=html
```

All tests must pass. Coverage output is written to `htmlcov/` for inspection if needed.

---

## 3. Mandatory Workflow

Follow this sequence for every task, no matter how small:

1. **Implement the change** following the project conventions in `feature-guide.md`.
2. **Run `make lint && make format && make test`** in the project root.
3. **Fix every failure autonomously** — see Section 4 for specific remedies.
4. **Re-run the full sequence** until all three gates exit with code 0.
5. **Only then report the task as complete** to the user.

Never hand control back to the user while any gate is failing. Never ask the user to run the quality gates themselves.

---

## 4. Diagnosing and Fixing Failures

### 4.1 `markdownlint` Failures

Markdownlint checks all `.md` files in the repository, including files under `docs/`. Common violations and fixes:

| Violation | Typical cause | Fix |
| --- | --- | --- |
| `MD022` – Headings must be surrounded by blank lines | Missing blank line before or after a `#` heading | Add a blank line above and below every heading |
| `MD031` – Fenced code blocks must be surrounded by blank lines | Code block directly follows or precedes text | Add a blank line before the opening fence and after the closing fence |
| `MD032` – Lists must be surrounded by blank lines | List starts or ends without a surrounding blank line | Add blank lines |
| `MD013` – Line too long | Prose line exceeds configured limit | Wrap the line |
| `MD041` – First line must be a top-level heading | File does not start with `# Title` | Add the heading or check the file structure |

See `docs/agents/markdown-guidelines.md` for the project's full markdown conventions.

### 4.2 `flake8` Failures

Flake8 checks Python style and correctness. Common violations:

| Code | Meaning | Fix |
| --- | --- | --- |
| `F401` | Imported but unused | Remove the unused import |
| `F811` | Redefinition of unused name | Remove the duplicate definition or the earlier unused one |
| `E501` | Line too long (> 88 chars) | Break the line; use implicit continuation inside `()` or `[]` |
| `E302 / E303` | Wrong number of blank lines between top-level definitions | Add or remove blank lines as required |
| `F841` | Local variable assigned but never used | Remove the assignment or use the variable |
| `W291 / W293` | Trailing whitespace | Remove trailing spaces |

**Do not add `# noqa` suppression comments** unless the violation is a genuine false-positive and the reason is documented inline.

### 4.3 `isort` / `black` Failures

Both are fully automated. The fix is always:

```bash
make format
```

Then re-run `make lint` to confirm the files are now clean. Typical root causes:

- Imports added in the wrong section (stdlib, third-party, local).
- Long import lines that need splitting.
- Trailing commas or spacing inconsistencies.

Never manually reorder imports or reformat code to match black's output — let the tool do it.

### 4.4 Test Failures

Test failures require understanding the root cause before acting. Follow this decision tree:

```text
Test fails
  ├─ Was the test correct before my change?
  │   ├─ YES → I broke existing behavior → fix the implementation to restore it
  │   └─ NO  → Test was already broken (pre-existing) → fix the test to match correct behavior
  │
  ├─ Is this a new test I wrote?
  │   └─ Fix the test or the implementation so they agree on the correct behavior
  │
  └─ Is this an indirect breakage (e.g., I changed a shared fixture or schema)?
      └─ Fix every affected test; do not patch individual assertions in isolation
```

**Never do any of the following to make a failing test pass:**

- Add `@pytest.mark.skip` or `@pytest.mark.xfail`.
- Delete the test.
- Stub out the implementation with a dummy return value.
- Catch and swallow the exception that the test is asserting.

If a test reveals that the intended behavior is genuinely ambiguous, implement the behavior that best satisfies the feature specification and update the test to document it explicitly.

### 4.5 Import / Syntax Errors

If `pytest` fails at collection time (before any test runs), there is likely a Python syntax error or a broken import. Identify the file from the traceback and fix it directly. Rerun `make test` to confirm collection succeeds.

Common causes:

- Circular imports introduced by a new `composition.py` wiring.
- Missing `__init__.py` in a new module directory.
- A class or function referenced before it is defined.
- A typo in an import path.

### 4.6 Migration / Model Drift

If tests fail because of a missing column or table, the ORM model was changed but no Alembic migration was generated. Fix by:

1. Confirm the model is imported in `app/models.py`.
2. Generate the migration: `alembic revision --autogenerate -m "<description>"`.
3. Apply it: `alembic upgrade head`.
4. Re-run `make test`.

---

## 5. Scope of Application

The quality gate requirement applies without exception to:

| Change type | Applies? |
| --- | --- |
| New feature module | Yes — always (see `feature-guide.md` Step 13) |
| Bug fix | Yes |
| Refactor (no behavior change) | Yes |
| Schema / model change | Yes |
| Policy or service update | Yes |
| New or modified test | Yes |
| Documentation (`.md`) change | Yes — `make lint` checks markdown too |
| `composition.py` wiring change | Yes |
| `main.py` router registration | Yes |
| Alembic migration script | Yes |

The only files excluded from Python linting and formatting are those outside `app/` (e.g., `alembic/`, `tests/`, `seeds/`). However, `tests/` is still exercised by `make test`, and all `.md` files are still checked by `markdownlint`.

---

## 6. Handling Pre-existing Failures

If, upon running the quality gates, failures are detected that pre-date the current task:

1. **Lint / formatting failures in files outside the current change** — fix them. Style debt is always in scope.
2. **Test failures that pre-date the change** — fix them if the root cause is clear. If the failure is complex and unrelated to the current task, document it in the task report and flag it explicitly; do not silently ignore it.
3. **Never leave the repository in a worse state than you found it.** If you cannot fix a pre-existing failure without significantly expanding scope, at minimum do not introduce additional failures.

---

## 7. Quick Reference

```bash
# Run all quality gates
make lint && make format && make test

# Fix formatting, then re-lint
make format && make lint

# Run only tests (useful mid-fix iteration)
make test

# Run a single test file during debugging
source .venv/bin/activate && python -m pytest tests/<module>/test_<file>.py -v

# Run tests matching a name pattern
source .venv/bin/activate && python -m pytest tests/ -k "<test_name_substring>" -v
```
